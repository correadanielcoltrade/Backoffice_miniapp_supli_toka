from django.db import models


class PaymentTransaction(models.Model):
    """
    Modulo de Seguimiento de Transacciones de Pagos.
    Campos clave: Id Cliente, Nombre Cliente, # Pago, Estado de Pago.
    Los pagos son confirmados por el backend de Toka mediante un webhook.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        CONFIRMED = "CONFIRMED", "Confirmado / Pagado"
        FAILED = "FAILED", "Fallido"
        REFUNDED = "REFUNDED", "Reembolsado"

    toka_customer_id = models.CharField("ID cliente", max_length=64, db_index=True)
    customer_name = models.CharField("nombre cliente", max_length=200)
    payment_number = models.CharField(
        "numero de pago", max_length=80, unique=True, db_index=True,
        help_text="merchantTransId: nuestro id unico de la transaccion.",
    )
    provider_payment_id = models.CharField(
        "paymentId de Toka", max_length=80, blank=True, default="", db_index=True,
        help_text="Id de pago que devuelve Toka. Es la llave para consultar "
                  "el estado del pago y para reembolsar.",
    )
    amount = models.DecimalField(
        "monto", max_digits=12, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        "estado de pago",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    raw_payload = models.JSONField("payload recibido", default=dict, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "transaccion de pago"
        verbose_name_plural = "transacciones de pago"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_number} - {self.get_status_display()}"
