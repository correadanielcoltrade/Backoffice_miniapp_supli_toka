"""
Endpoints 2 y 10 de Wigilabs: createOrder (pago) y Payment status.

  POST /v1/payments/createOrder             -> crea el pedido + inicia el pago
  GET  /v1/orders/{orderId}/paymentStatus   -> estado REAL del pago (via Toka)

Ambos requieren Bearer sessionToken. El monto SIEMPRE se calcula en el servidor
a partir de productIdVariant (el front nunca envia montos). La llamada de pago a
Toka usa create_payment/query_payment del TokaClient; mientras no exista el
appId del mini-program (TOKA_APP_ID) esas llamadas responden TOKA_UNAVAILABLE,
igual que Apply Token / Query User Info. Todo lo demas ya queda operativo.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.exceptions import NotFound, ValidationError

from apps.orders.models import CustomerAddress, Order, OrderItem
from apps.catalog.models import Product
from apps.payments.models import PaymentTransaction
from apps.toka.client import TokaAPIError, TokaClient

from .base import MiniAppAuthView
from .envelope import data_response, error_response
from .services_payment import (
    TOKA_TO_PAYMENT_STATUS,
    confirm_order_paid,
    mark_order_cancelled,
    mark_order_payment_failed,
)
from .toka_utils import toka_error_to_response


def _payment_amount(data, order):
    """
    Toka devuelve paymentAmount en CENTAVOS; el contrato con Wigilabs pide el
    monto en MXN. Toka lo manda en DOS formas segun el endpoint:
      - objeto:  {"value": 2000, "currency": "MXN"}  (createOrder / notify)
      - entero:  2000                                 (query/inquiry de pago)
    Se soportan ambos. Si Toka no lo trae, se usa el total del pedido.
    """
    block = data.get("paymentAmount")
    if isinstance(block, dict):
        value = block.get("value")
        currency = block.get("currency", "MXN")
    else:
        # Entero/numero plano (o None si no viene).
        value = block
        currency = "MXN"
    if value is None or value == "":
        return {"value": str(order.total_amount), "currency": "MXN"}
    pesos = (Decimal(str(value)) / 100).quantize(Decimal("0.01"))
    return {"value": str(pesos), "currency": currency}


class _TokaRejected(Exception):
    """Toka respondio pero rechazo el pago (resultStatus != 'S')."""

    def __init__(self, resp):
        self.resp = resp


# Ventana para considerar un createOrder repetido como "misma solicitud".
_DUPLICATE_WINDOW_MIN = 10


def _find_duplicate_pending(customer, address, items):
    """
    Idempotencia (spec 20030001): busca un pedido PENDING reciente del mismo
    cliente, con la MISMA direccion y el MISMO conjunto de productos/cantidades.
    Evita duplicar el pago ante un doble submit del front. Best-effort (no cubre
    carreras concurrentes exactas; eso requeriria un constraint/lock adicional).
    """
    signature = sorted((p.id, q) for p, q, _ in items)
    since = timezone.now() - timedelta(minutes=_DUPLICATE_WINDOW_MIN)
    candidates = (
        customer.orders
        .filter(status=Order.Status.PENDING, saved_address=address,
                created_at__gte=since)
        .prefetch_related("items")
    )
    for order in candidates:
        existing = sorted((i.product_id, i.quantity) for i in order.items.all())
        if existing == signature:
            return order
    return None


def _resolve_address(customer, address_id):
    """Direccion guardada del usuario. Inexistente o ajena -> 404 (mismo codigo)."""
    if not address_id:
        raise ValidationError({"addressId": "Campo obligatorio."})
    try:
        return customer.addresses.get(pk=address_id)
    except (CustomerAddress.DoesNotExist, ValueError, TypeError):
        raise NotFound("Direccion no encontrada.")


def _resolve_items(products):
    """
    Convierte products[] del request en [(Product, quantity, unit_price)].
    El precio se toma del catalogo (MXN); el front nunca envia montos.
    """
    if not isinstance(products, list) or not products:
        raise ValidationError({"products": "Debe incluir al menos un producto."})
    resolved = []
    for idx, entry in enumerate(products):
        variant_id = (entry or {}).get("productIdVariant")
        quantity = (entry or {}).get("quantity")
        if not variant_id or not isinstance(quantity, int) or quantity < 1:
            raise ValidationError({
                f"products[{idx}]": "productIdVariant y quantity (>=1) son obligatorios."
            })
        # Sin modelo de variantes: productIdVariant == productId (ver ProductDetail).
        try:
            product = Product.objects.select_related("brand", "inventory").get(
                id=variant_id, is_active=True
            )
        except (Product.DoesNotExist, ValueError, TypeError):
            raise ValidationError({
                f"products[{idx}].productIdVariant": "Producto/variante inexistente."
            })
        resolved.append((product, quantity, product.sale_price))
    return resolved


def _stock_issues(items):
    """
    Recibe items resueltos [(Product, qty, price)] y devuelve la lista de
    productos cuya cantidad solicitada supera el stock disponible. Lista vacia =
    todo tiene stock. 'Sin inventario' cuenta como stock 0.
    """
    issues = []
    for product, qty, _ in items:
        inv = getattr(product, "inventory", None)
        available = inv.units_in_stock if inv else 0
        if qty > available:
            issues.append({
                "productIdVariant": str(product.id),
                "name": product.description,
                "requested": qty,
                "available": available,
            })
    return issues


class ValidateStockView(MiniAppAuthView):
    """
    POST /v1/payments/validate-stock

    Valida el carrito ANTES de crear la orden: compara la cantidad solicitada de
    cada producto contra el stock disponible. Devuelve valid=true solo si TODOS
    los productos tienen stock suficiente. No crea nada ni inicia ningun pago.

    Body: {"products": [{"productIdVariant": "1", "quantity": 3}, ...]}
    """

    def post(self, request):
        items = _resolve_items((request.data or {}).get("products"))
        result = []
        valid = True
        for product, qty, _ in items:
            inv = getattr(product, "inventory", None)
            available = inv.units_in_stock if inv else 0
            ok = qty <= available
            valid = valid and ok
            result.append({
                "productIdVariant": str(product.id),
                "name": product.description,
                "requested": qty,
                "available": available,
                "isAvailable": ok,
            })
        return data_response({"valid": valid, "items": result})


class CreateOrderView(MiniAppAuthView):
    """Endpoint 2 — POST /v1/payments/createOrder."""

    def post(self, request):
        customer = request.user
        body = request.data or {}

        contact_name = (body.get("contactName") or "").strip()
        if not contact_name:
            raise ValidationError({"contactName": "Campo obligatorio."})
        phone = body.get("contactPhone") or {}
        country_code = (phone.get("countryCode") or "").strip()
        number = (phone.get("number") or "").strip()
        if not country_code or not number:
            raise ValidationError({
                "contactPhone": "countryCode y number son obligatorios."
            })

        address = _resolve_address(customer, body.get("addressId"))
        items = _resolve_items(body.get("products"))
        total = sum(price * qty for _, qty, price in items)
        contact_number = f"{country_code} {number}".strip()[:30]

        # Valida stock ANTES de crear la orden e iniciar el pago en Toka: si el
        # cliente pide mas unidades que el stock, no se procesa la orden.
        issues = _stock_issues(items)
        if issues:
            return error_response(
                "INSUFFICIENT_STOCK",
                "No hay stock suficiente para uno o mas productos del pedido.",
                details=issues,
                status=http_status.HTTP_409_CONFLICT,
            )

        # Idempotencia: no duplicar un pago ya iniciado para el mismo carrito.
        if _find_duplicate_pending(customer, address, items):
            return error_response(
                "20030001",
                "Repeated submission, and a payment order already exists.",
                status=http_status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    saved_address=address,
                    recipient_name=contact_name,
                    contact_number=contact_number,
                    full_address=address.complete_address,
                    address_complement=address.supplementary_address,
                    colonia=address.suburb,
                    city_alcaldia=address.municipality,
                    state=address.state,
                    postal_code=address.zip_code,
                    status=Order.Status.PENDING,
                    total_amount=total,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=p, quantity=q, unit_price=price)
                    for p, q, price in items
                ])

                # Iniciar el pago en Toka (Mini-Program Payment).
                # merchantTransId (campo customizable de Toka, <=64): usamos el
                # consecutivo legible del pedido, SUPLI-000123.
                merchant_trans_id = order.order_number
                client = TokaClient()
                resp = client.create_payment(
                    user_id=customer.toka_customer_id,  # userId de Toka
                    merchant_trans_id=merchant_trans_id,
                    amount=total,
                    order_title=f"Pedido {order.order_number}",
                )
                # El camino feliz del create devuelve "A" (20000006 Accept Request),
                # no "S". Ambos son exito.
                if resp.result_status not in ("S", "A"):
                    raise _TokaRejected(resp)

                payment_url = resp.data.get("paymentUrl", "")
                payment_id = resp.data.get("paymentId", "")
                PaymentTransaction.objects.create(
                    toka_customer_id=customer.toka_customer_id,
                    # Snapshot del nombre: preferimos el del pedido (recipient_name),
                    # el full_name del Customer aun es el id de Toka mientras no
                    # tengamos el nombre desde la super app (Query User Info).
                    customer_name=order.recipient_name or customer.full_name,
                    payment_number=merchant_trans_id,
                    provider_payment_id=payment_id,
                    amount=total,
                    status=PaymentTransaction.Status.PENDING,
                    order=order,
                    raw_payload=resp.data,
                )
        except _TokaRejected as exc:
            return toka_error_to_response(exc.resp)
        except TokaAPIError as exc:
            return error_response("TOKA_UNAVAILABLE", str(exc), status=502)

        return data_response(
            {"orderId": str(order.id), "paymentUrl": payment_url},
            status=http_status.HTTP_201_CREATED,
        )


class PaymentStatusView(MiniAppAuthView):
    """Endpoint 10 — GET /v1/orders/{orderId}/paymentStatus."""

    def get(self, request, order_id):
        customer = request.user
        try:
            order = customer.orders.get(pk=order_id)
        except (Order.DoesNotExist, ValueError, TypeError):
            raise NotFound("Pedido no encontrado.")

        payment = order.payments.order_by("-created_at").first()
        if not payment:
            raise NotFound("El pedido no tiene un pago iniciado.")
        if not payment.provider_payment_id:
            raise NotFound("El pago del pedido no tiene paymentId de Toka.")

        client = TokaClient()
        try:
            # Fuente de verdad: la consulta al backend de Toka (nunca my.pay).
            resp = client.query_payment(payment_id=payment.provider_payment_id)
        except TokaAPIError as exc:
            return error_response("TOKA_UNAVAILABLE", str(exc), status=502)
        if resp.result_status not in ("S", "A", ""):
            return toka_error_to_response(resp)

        data = resp.data or {}
        status = TOKA_TO_PAYMENT_STATUS.get(data.get("paymentStatus"), "PROCESSING")

        # Reconciliar el estado local con lo que dice Toka.
        if status == "SUCCESS":
            _, err = confirm_order_paid(
                order, payment_number=payment.payment_number, raw_payload=data
            )
            if err:
                return error_response(
                    "STOCK_CONFLICT", err, status=http_status.HTTP_409_CONFLICT
                )
        elif status == "FAILED":
            mark_order_payment_failed(
                order, payment_number=payment.payment_number, raw_payload=data
            )

        return data_response({
            "orderId": str(order.id),
            "paymentId": data.get("paymentId", payment.provider_payment_id),
            "status": status,
            "paymentAmount": _payment_amount(data, order),
            "paymentTime": data.get("paymentTime"),
            # Detalle del pago si viene; si no, el resultado de la llamada.
            "resultCode": data.get("paymentResultCode") or resp.result_code,
            "resultMessage": (
                data.get("paymentResultMessage") or resp.result_message
            ),
        })


def _cancel_payload(order, toka_close):
    return {
        "orderId": str(order.id),
        "orderNumber": order.order_number,
        "status": Order.Status.CANCELLED,
        "tokaClose": toka_close,
    }


class CancelOrderView(MiniAppAuthView):
    """
    POST /v1/orders/{orderId}/cancel

    Cancela un pedido cuyo pago NO se completo (error de Toka o el usuario
    cancelo). Cierra el pago en Toka (best-effort) y marca el pedido CANCELLED,
    liberando el bloqueo de idempotencia (_find_duplicate_pending) para que el
    usuario pueda iniciar otra compra de inmediato.

    Es POST (no DELETE) porque Alipay solo soporta GET/POST.
    """

    def post(self, request, order_id):
        customer = request.user
        try:
            order = customer.orders.get(pk=order_id)
        except (Order.DoesNotExist, ValueError, TypeError):
            raise NotFound("Pedido no encontrado.")

        # Idempotente: si ya esta cancelado, exito (sin volver a llamar a Toka).
        if order.status == Order.Status.CANCELLED:
            return data_response(_cancel_payload(order, "already"))

        # No se cancela un pedido ya pagado o en proceso de entrega.
        if order.status != Order.Status.PENDING:
            return error_response(
                "ORDER_NOT_CANCELABLE",
                "Solo se puede cancelar un pedido pendiente de pago.",
                status=http_status.HTTP_409_CONFLICT,
            )

        # Cerrar el pago en Toka. Best-effort: si Toka no responde igual
        # cancelamos localmente (ademas la orden en Toka expira sola por
        # expiryTime); asi el usuario nunca queda bloqueado.
        toka_close = "skipped"
        payment = order.payments.order_by("-created_at").first()
        if payment and payment.provider_payment_id:
            try:
                resp = TokaClient().close_payment(
                    payment_id=payment.provider_payment_id
                )
                toka_close = (
                    "closed"
                    if resp.result_status in ("S", "A", "")
                    else f"rejected:{resp.result_code}"
                )
            except TokaAPIError:
                toka_close = "unavailable"

        mark_order_cancelled(order)
        return data_response(_cancel_payload(order, toka_close))
