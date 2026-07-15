"""Servicios de dominio para el inventario."""
from django.db import transaction
from django.db.models import F

from .models import Inventory, StockMovement


class InsufficientStockError(Exception):
    """No hay suficientes unidades para descontar."""


@transaction.atomic
def apply_stock_change(product, change, reason, reference=""):
    """
    Aplica un cambio de stock de forma atomica y registra el movimiento.
    `change` puede ser negativo (venta/salida) o positivo (devolucion/ingreso).
    """
    inventory = (
        Inventory.objects.select_for_update().get(product=product)
    )
    new_total = inventory.units_in_stock + change
    if new_total < 0:
        raise InsufficientStockError(
            f"Stock insuficiente para {product.sku}: "
            f"disponible {inventory.units_in_stock}, requerido {abs(change)}."
        )
    Inventory.objects.filter(pk=inventory.pk).update(
        units_in_stock=F("units_in_stock") + change
    )
    StockMovement.objects.create(
        inventory=inventory,
        change=change,
        reason=reason,
        reference=reference,
    )
    inventory.refresh_from_db()
    return inventory


def deduct_for_paid_order(order, reference=""):
    """
    Descuenta el stock de todos los items de un pedido pagado.
    Se invoca desde el webhook de confirmacion de pago de Toka.
    """
    for item in order.items.select_related("product"):
        apply_stock_change(
            product=item.product,
            change=-item.quantity,
            reason=StockMovement.Reason.SALE_PAID,
            reference=reference or f"Pedido #{order.id}",
        )
