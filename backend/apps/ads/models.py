from django.db import models

MAX_CAROUSEL_IMAGES = 4


class Carousel(models.Model):
    """
    Carrusel de Ads para la mini app.
    Permite cargar hasta 4 fotos y define el tamano (ancho x alto) del carrusel.
    """

    name = models.CharField("nombre", max_length=120)
    width = models.PositiveIntegerField("ancho (px)", default=1080)
    height = models.PositiveIntegerField("alto (px)", default=1080)
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "carrusel"
        verbose_name_plural = "carruseles"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class CarouselImage(models.Model):
    """Imagen del carrusel. Maximo 4 por carrusel (validado en el serializer)."""

    carousel = models.ForeignKey(
        Carousel, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField("imagen", upload_to="ads/carousel/")
    link_url = models.URLField("url de destino", blank=True)
    position = models.PositiveSmallIntegerField("posicion", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "imagen de carrusel"
        verbose_name_plural = "imagenes de carrusel"
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.carousel.name} #{self.position}"
