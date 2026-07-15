"""
Serializacion de pedidos al contrato Wigilabs (Endpoints 9 y 15).

Order history y Order detail comparten la misma base (orderId, date, status,
totalAmount, items[]); el detalle agrega tracking/carrier/shippingCost cuando
existan. Los datos de producto de cada item se toman del catalogo actual salvo
el precio unitario, que SI queda congelado al momento de la compra (OrderItem).
"""
from datetime import timezone as _tz

from .serializers import CURRENCY, _first_image
from .services_payment import ORDER_TO_DELIVERY_STATUS


def _iso(dt):
    """Formatea un datetime a ISO-8601 UTC con sufijo Z (2026-06-30T18:22:00Z)."""
    if not dt:
        return None
    return dt.astimezone(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _money(value):
    return {"value": str(value), "currency": CURRENCY}


def serialize_order_item(item, request=None):
    """Un item de pedido: datos de producto + precio congelado de compra."""
    product = item.product
    return {
        "productIdVariant": str(product.id),
        "name": product.description,
        "brand": product.brand.name if product.brand_id else "",
        "imageUrl": _first_image(request, product),
        "quantity": item.quantity,
        "unitPrice": _money(item.unit_price),
    }


def serialize_order_summary(order, request=None):
    """Endpoint 9 (Order history): tarjeta de pedido."""
    return {
        "orderId": str(order.id),
        "date": _iso(order.created_at),
        "status": ORDER_TO_DELIVERY_STATUS.get(order.status, "IN_PROGRESS"),
        "totalAmount": _money(order.total_amount),
        "items": [serialize_order_item(i, request) for i in order.items.all()],
    }


def serialize_order_detail(order, request=None):
    """
    Endpoint 15 (Order detail): todo lo del historial + envio/tracking cuando
    exista. Nuestro modelo aun no persiste carrier/trackingUrl/shippingCost, asi
    que se omiten (la spec los marca como opcionales / "pueden no existir aun").
    """
    data = serialize_order_summary(order, request)
    # Los campos opcionales de envio se agregaran aqui cuando el pedido se
    # despache (trackingUrl, carrier, shippingCost). Hoy no se modelan.
    return data
