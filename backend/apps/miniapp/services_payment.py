"""
Servicios de pago del BFF (Fase 4).

Confirmacion de pago reutilizable: marca el pedido como PAGADO y descuenta el
inventario UNA sola vez, igual que el webhook de Toka (apps/payments/views.py).
La consulta de Payment status (Endpoint 10) la usa cuando Toka reporta SUCCESS,
como alternativa "consulta interna" a esperar el webhook (ver Nota 18 de la spec).
"""
from django.db import transaction
from django.utils import timezone

from apps.inventory.services import InsufficientStockError, deduct_for_paid_order
from apps.orders.models import Order
from apps.payments.models import PaymentTransaction

# --- Mapeos de estado ---------------------------------------------------------
# Estado de PAGO que Toka (AMS) devuelve  ->  status del contrato Wigilabs.
TOKA_TO_PAYMENT_STATUS = {
    "SUCCESS": "SUCCESS",
    "S": "SUCCESS",
    "PROCESSING": "PROCESSING",
    "PENDING": "PROCESSING",
    "U": "PROCESSING",
    "FAIL": "FAILED",
    "FAILED": "FAILED",
    "CANCELLED": "FAILED",
    "F": "FAILED",
}

# Estado interno del pedido  ->  estado de ENTREGA del contrato (IN_PROGRESS/DELIVERED).
ORDER_TO_DELIVERY_STATUS = {
    Order.Status.PAID: "IN_PROGRESS",
    Order.Status.PREPARING: "IN_PROGRESS",
    Order.Status.SHIPPED: "IN_PROGRESS",
    Order.Status.DELIVERED: "DELIVERED",
}
# Filtro inverso: los estados internos que corresponden a cada estado de entrega.
DELIVERY_STATUS_TO_ORDER = {
    "IN_PROGRESS": [Order.Status.PAID, Order.Status.PREPARING, Order.Status.SHIPPED],
    "DELIVERED": [Order.Status.DELIVERED],
}
# Estados que aparecen en el historial (pedidos ya "realizados"/pagados).
HISTORY_ORDER_STATUSES = [
    Order.Status.PAID,
    Order.Status.PREPARING,
    Order.Status.SHIPPED,
    Order.Status.DELIVERED,
]


def confirm_order_paid(order, *, payment_number, amount=None, raw_payload=None):
    """
    Confirma el pago de un pedido de forma idempotente:
      1. Registra/actualiza la PaymentTransaction como CONFIRMED.
      2. Marca el pedido como PAGADO y descuenta inventario (una sola vez).

    Devuelve (payment, error_message). Si el inventario es insuficiente, no
    confirma y devuelve el mensaje de error (para responder 409).
    """
    with transaction.atomic():
        payment, _ = PaymentTransaction.objects.select_for_update().update_or_create(
            payment_number=payment_number,
            defaults={
                "toka_customer_id": order.customer.toka_customer_id,
                "customer_name": order.customer.full_name,
                "amount": amount if amount is not None else order.total_amount,
                "status": PaymentTransaction.Status.CONFIRMED,
                "order": order,
                "confirmed_at": timezone.now(),
                "raw_payload": raw_payload or {},
            },
        )

        locked = Order.objects.select_for_update().get(pk=order.pk)
        if not locked.stock_deducted:
            try:
                deduct_for_paid_order(locked, reference=payment.payment_number)
            except InsufficientStockError as exc:
                transaction.set_rollback(True)
                return None, str(exc)
            locked.status = Order.Status.PAID
            locked.stock_deducted = True
            locked.save(update_fields=["status", "stock_deducted", "updated_at"])

    return payment, None


def mark_order_payment_failed(order, *, payment_number, amount=None, raw_payload=None):
    """Registra la transaccion como fallida (sin tocar inventario ni el pedido)."""
    PaymentTransaction.objects.update_or_create(
        payment_number=payment_number,
        defaults={
            "toka_customer_id": order.customer.toka_customer_id,
            "customer_name": order.customer.full_name,
            "amount": amount if amount is not None else order.total_amount,
            "status": PaymentTransaction.Status.FAILED,
            "order": order,
            "raw_payload": raw_payload or {},
        },
    )
