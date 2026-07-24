from rest_framework import serializers

from .models import (
    BANNER_HEIGHT,
    BANNER_WIDTH,
    MAX_CAROUSEL_IMAGES,
    Carousel,
    CarouselImage,
)


class CarouselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselImage
        fields = ["id", "carousel", "image", "link_url", "position", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        carousel = attrs.get("carousel") or getattr(self.instance, "carousel", None)
        if carousel and self.instance is None:
            if carousel.images.count() >= MAX_CAROUSEL_IMAGES:
                raise serializers.ValidationError(
                    f"El carrusel solo permite {MAX_CAROUSEL_IMAGES} imagenes."
                )
        self._validate_dimensions(attrs.get("image"))
        return attrs

    @staticmethod
    def _validate_dimensions(image):
        """
        Rechaza cualquier banner que no mida EXACTAMENTE BANNER_WIDTH x
        BANNER_HEIGHT px. Solo corre cuando llega una imagen nueva (en un PATCH
        que solo cambia link_url, `image` es None y no se valida).
        """
        if image is None:
            return
        # El campo ImageField ya abrio la imagen con Pillow al validarla, asi que
        # reutilizamos esa instancia (no consume el puntero del archivo). Si no
        # estuviera disponible, la abrimos y devolvemos el puntero a 0.
        pil = getattr(image, "image", None)
        if pil is not None:
            width, height = pil.size
        else:
            from PIL import Image

            image.seek(0)
            with Image.open(image) as img:
                width, height = img.size
            image.seek(0)
        if (width, height) != (BANNER_WIDTH, BANNER_HEIGHT):
            raise serializers.ValidationError(
                {
                    "image": (
                        f"El banner debe medir exactamente {BANNER_WIDTH}x"
                        f"{BANNER_HEIGHT} px. La imagen que subiste mide "
                        f"{width}x{height} px."
                    )
                }
            )


class CarouselSerializer(serializers.ModelSerializer):
    images = CarouselImageSerializer(many=True, read_only=True)

    class Meta:
        model = Carousel
        fields = [
            "id",
            "name",
            "width",
            "height",
            "is_active",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
