from django.db import models

MAX_CAROUSEL_IMAGES = 4

# Dimensiones EXACTAS (px) que debe tener cada banner del carrusel.
# Cualquier imagen con otro tamano se rechaza al subir (ver serializers.py).
BANNER_WIDTH = 1380
BANNER_HEIGHT = 440


class Carousel(models.Model):
    """
    Carrusel de Ads para la mini app.
    Permite cargar hasta 4 fotos y define el tamano (ancho x alto) del carrusel.
    """

    name = models.CharField("nombre", max_length=120)
    # Los banners tienen un tamano fijo (BANNER_WIDTH x BANNER_HEIGHT), asi que
    # el carrusel usa esas mismas dimensiones por defecto; ya no se piden al crear.
    width = models.PositiveIntegerField("ancho (px)", default=BANNER_WIDTH)
    height = models.PositiveIntegerField("alto (px)", default=BANNER_HEIGHT)
    # Interruptor maestro manual.
    is_active = models.BooleanField("activo", default=True)
    # Programacion de vigencia (opcional). El carrusel se sirve a la mini app solo
    # si is_active Y estamos dentro de la ventana [active_from, active_until].
    # Cualquiera de las dos puede quedar vacia (sin limite por ese lado).
    active_from = models.DateTimeField("activar desde", null=True, blank=True)
    active_until = models.DateTimeField("desactivar el", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "carrusel"
        verbose_name_plural = "carruseles"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def schedule_status(self, now=None):
        """
        Estado EFECTIVO del carrusel considerando el interruptor y la ventana:
          INACTIVE  -> apagado manualmente (is_active=False).
          SCHEDULED -> activo pero aun no llega active_from.
          EXPIRED   -> activo pero ya paso active_until.
          ACTIVE    -> se esta sirviendo ahora mismo.
        """
        from django.utils import timezone

        if not self.is_active:
            return "INACTIVE"
        now = now or timezone.now()
        if self.active_from and now < self.active_from:
            return "SCHEDULED"
        if self.active_until and now > self.active_until:
            return "EXPIRED"
        return "ACTIVE"


class CarouselImage(models.Model):
    """Imagen del carrusel. Maximo 4 por carrusel (validado en el serializer)."""

    class TargetType(models.TextChoices):
        CATEGORY = "CATEGORY", "Categoria"
        BRAND = "BRAND", "Marca"
        PRODUCT = "PRODUCT", "Producto"

    carousel = models.ForeignKey(
        Carousel, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField("imagen", upload_to="ads/carousel/")
    link_url = models.URLField("url de destino", blank=True)
    # Destino del tap en la mini app: a que contenido navega (categoria/marca/
    # producto) al tocar el banner. Vacio = el banner no navega a nada.
    target_type = models.CharField(
        "tipo de destino", max_length=10,
        choices=TargetType.choices, blank=True, default="",
    )
    target_id = models.PositiveIntegerField(
        "id de destino", null=True, blank=True,
        help_text="Id de la categoria, marca o producto al que navega el tap.",
    )
    position = models.PositiveSmallIntegerField("posicion", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "imagen de carrusel"
        verbose_name_plural = "imagenes de carrusel"
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.carousel.name} #{self.position}"
