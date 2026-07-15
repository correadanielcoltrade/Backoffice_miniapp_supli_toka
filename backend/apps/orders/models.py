from django.core.validators import MinValueValidator
from django.db import models


class Customer(models.Model):
    """
    Cliente de la mini app. Los datos base provienen de la super app de Toka
    (via API) y se sincronizan/almacenan aqui para operar el back office.
    """

    toka_customer_id = models.CharField(
        "ID cliente Toka", max_length=64, unique=True, db_index=True
    )
    full_name = models.CharField("nombre completo", max_length=200)
    contact_number = models.CharField("numero de contacto", max_length=30, blank=True)
    email = models.EmailField("correo", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.toka_customer_id})"


class CustomerAddress(models.Model):
    """
    Direccion de entrega del cliente, en formato mexicano (segun la spec de
    Wigilabs). El cliente la administra desde la mini-app (maximo 3). Los campos
    mapean 1:1 con los del BFF /v1/users/me/addresses.
    """

    MAX_PER_CUSTOMER = 3

    class Label(models.TextChoices):
        HOME = "HOME", "Casa"
        OFFICE = "OFFICE", "Oficina"
        UNIVERSITY = "UNIVERSITY", "Universidad"
        OTHER = "OTHER", "Otro"

    customer = models.ForeignKey(
        Customer,
        verbose_name="cliente",
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        "etiqueta", max_length=20, choices=Label.choices, default=Label.HOME
    )
    custom_label = models.CharField(
        "etiqueta personalizada", max_length=60, blank=True, default="",
        help_text="Se usa cuando la etiqueta es 'Otro'.",
    )
    complete_address = models.CharField(
        "direccion (calle y numero)", max_length=255, default=""
    )
    no_street_number = models.BooleanField("sin numero", default=False)
    state = models.CharField("estado", max_length=120, default="")
    municipality = models.CharField(
        "municipio / alcaldia", max_length=120, default=""
    )
    locality = models.CharField(
        "localidad", max_length=120, blank=True, default=""
    )
    suburb = models.CharField("colonia", max_length=120, default="")
    zip_code = models.CharField(
        "codigo postal", max_length=10, blank=True, default=""
    )
    unknown_zip_code = models.BooleanField("no conoce el CP", default=False)
    supplementary_address = models.CharField(
        "complemento (interior, referencias)", max_length=255, blank=True, default=""
    )
    delivery_instructions = models.TextField(
        "instrucciones de entrega", blank=True, default=""
    )
    is_default = models.BooleanField("predeterminada", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "direccion de cliente"
        verbose_name_plural = "direcciones de clientes"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.customer.full_name} - {self.complete_address}"


class Order(models.Model):
    """
    Pedido. Guarda una copia (snapshot) de la direccion de entrega para que sea
    editable sin afectar la direccion guardada del cliente, y opcionalmente
    referencia la direccion guardada seleccionada.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente de pago"
        PAID = "PAID", "Pagado"
        PREPARING = "PREPARING", "En preparacion"
        SHIPPED = "SHIPPED", "Enviado"
        DELIVERED = "DELIVERED", "Entregado"
        CANCELLED = "CANCELLED", "Cancelado"

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    saved_address = models.ForeignKey(
        CustomerAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Direccion guardada seleccionada por el cliente (opcional)",
    )

    # Snapshot editable de la direccion de entrega (los 8 campos traidos de Toka).
    # Todos son obligatorios excepto el complemento de direccion.
    recipient_name = models.CharField("nombre completo", max_length=200)
    contact_number = models.CharField("numero de contacto", max_length=30)
    full_address = models.CharField("direccion completa", max_length=255)
    address_complement = models.CharField(
        "complemento de direccion", max_length=255, blank=True
    )
    colonia = models.CharField("colonia", max_length=120)
    city_alcaldia = models.CharField("ciudad / alcaldia", max_length=120)
    state = models.CharField("estado", max_length=120)
    postal_code = models.CharField("codigo postal", max_length=10)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    total_amount = models.DecimalField(
        "monto total", max_digits=12, decimal_places=2, default=0
    )
    stock_deducted = models.BooleanField(
        "stock descontado", default=False,
        help_text="True una vez que el pago fue confirmado y se descuento inventario.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{self.pk} - {self.customer.full_name}"

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), 0)
        self.total_amount = total
        self.save(update_fields=["total_amount", "updated_at"])
        return total


class OrderItem(models.Model):
    """Linea de un pedido."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(
        "cantidad", validators=[MinValueValidator(1)], default=1
    )
    unit_price = models.DecimalField("precio unitario", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "linea de pedido"
        verbose_name_plural = "lineas de pedido"

    def __str__(self):
        return f"{self.product.sku} x{self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
