from django.db import models


class Inventory(models.Model):
    """
    Inventario por producto.
    Muestra: Descripcion del producto y SKU (via relacion con Product) y
    las Unidades en inventario (campo editable).

    Nota de negocio: una unidad comprada en la mini app se descuenta del
    inventario luego de que Toka confirma el pago (ver movimiento StockMovement
    disparado desde el webhook de pagos).
    """

    product = models.OneToOneField(
        "catalog.Product",
        verbose_name="producto",
        on_delete=models.CASCADE,
        related_name="inventory",
    )
    units_in_stock = models.PositiveIntegerField("unidades en inventario", default=0)
    reorder_level = models.PositiveIntegerField("nivel de reorden", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "inventario"
        verbose_name_plural = "inventarios"
        ordering = ["product__description"]

    def __str__(self):
        return f"{self.product.sku}: {self.units_in_stock} u."


class StockMovement(models.Model):
    """Historial de movimientos de stock (auditoria)."""

    class Reason(models.TextChoices):
        SALE_PAID = "SALE_PAID", "Venta pagada (mini app)"
        MANUAL = "MANUAL", "Ajuste manual"
        RETURN = "RETURN", "Devolucion / logistica inversa"
        INITIAL = "INITIAL", "Carga inicial"

    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="movements"
    )
    change = models.IntegerField("cambio (+/-)")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    reference = models.CharField(
        "referencia", max_length=120, blank=True,
        help_text="Ej. numero de pago o pedido relacionado",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "movimiento de stock"
        verbose_name_plural = "movimientos de stock"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.inventory.product.sku} {self.change:+d} ({self.get_reason_display()})"
