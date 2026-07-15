from django.db import models


class ReturnRequest(models.Model):
    """
    Modulo de Logistica Inversa (devoluciones).
    NOTA: campos pendientes por confirmar con el negocio. Se deja una estructura
    base ampliable. Al aprobar una devolucion se puede reingresar stock via
    apps.inventory.services.apply_stock_change (reason=RETURN).
    """

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Solicitada"
        APPROVED = "APPROVED", "Aprobada"
        RECEIVED = "RECEIVED", "Recibida"
        REFUNDED = "REFUNDED", "Reembolsada"
        REJECTED = "REJECTED", "Rechazada"

    order = models.ForeignKey(
        "orders.Order", on_delete=models.PROTECT, related_name="return_requests"
    )
    reason = models.TextField("motivo", blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED
    )
    # TODO: agregar campos definitivos cuando el negocio los confirme.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "solicitud de devolucion"
        verbose_name_plural = "solicitudes de devolucion"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Devolucion pedido #{self.order_id} ({self.get_status_display()})"
