from django.db import models


class Category(models.Model):
    """Categoria de producto. Expone a la mini app: categoryId, sortOrder, name, iconUrl."""

    name = models.CharField("categoria", max_length=120, unique=True)
    # sortOrder e iconUrl que consume la mini app (Wigilabs).
    sort_order = models.PositiveIntegerField("orden", default=0)
    icon = models.ImageField(
        "icono", upload_to="catalog/categories/", blank=True, null=True
    )
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Brand(models.Model):
    """Marca de producto. Expone a la mini app: brandId, sortOrder, name, logoUrl."""

    name = models.CharField("marca", max_length=120, unique=True)
    sort_order = models.PositiveIntegerField("orden", default=0)
    logo = models.ImageField(
        "logo", upload_to="catalog/brands/", blank=True, null=True
    )
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "marca"
        verbose_name_plural = "marcas"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Producto del catalogo.
    Campos: Descripcion, SKU, Categoria, Precio de venta.
    El inventario vive en el modulo de inventario (apps.inventory) via
    relacion OneToOne para mantener separadas ambas responsabilidades.
    """

    # `description` es el NOMBRE que ve el usuario (Wigilabs: name).
    description = models.CharField("nombre / descripcion corta", max_length=255)
    # Descripcion larga para la ficha del producto (Wigilabs: description).
    long_description = models.TextField("descripcion larga", blank=True)
    sku = models.CharField("SKU", max_length=64, unique=True, db_index=True)
    category = models.ForeignKey(
        Category,
        verbose_name="categoria",
        on_delete=models.PROTECT,
        related_name="products",
    )
    brand = models.ForeignKey(
        Brand,
        verbose_name="marca",
        on_delete=models.PROTECT,
        related_name="products",
        blank=True,
        null=True,
    )
    sale_price = models.DecimalField(
        "precio de venta", max_digits=12, decimal_places=2
    )
    # Ficha tecnica (Wigilabs: features[] y specifications[]).
    features = models.JSONField("caracteristicas", default=list, blank=True)
    specifications = models.JSONField("especificaciones", default=list, blank=True)
    # Banderas que consume la mini app.
    is_featured = models.BooleanField("destacado", default=False)
    is_on_offer = models.BooleanField("en oferta", default=False)
    show_stock = models.BooleanField("mostrar stock", default=True)
    # Hasta 4 imagenes del producto (para galeria en la mini app)
    image1 = models.ImageField(
        "imagen 1", upload_to="catalog/products/", blank=True, null=True
    )
    image2 = models.ImageField(
        "imagen 2", upload_to="catalog/products/", blank=True, null=True
    )
    image3 = models.ImageField(
        "imagen 3", upload_to="catalog/products/", blank=True, null=True
    )
    image4 = models.ImageField(
        "imagen 4", upload_to="catalog/products/", blank=True, null=True
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["description"]

    def __str__(self):
        return f"{self.sku} - {self.description}"
