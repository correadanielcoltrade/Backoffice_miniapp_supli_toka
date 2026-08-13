from rest_framework import serializers

from apps.catalog.models import Brand, Category, Product

from .models import (
    BANNER_HEIGHT,
    BANNER_WIDTH,
    MAX_CAROUSEL_IMAGES,
    Carousel,
    CarouselImage,
)

# Modelo que respalda cada tipo de destino del tap del banner.
_TARGET_MODELS = {
    CarouselImage.TargetType.CATEGORY: Category,
    CarouselImage.TargetType.BRAND: Brand,
    CarouselImage.TargetType.PRODUCT: Product,
}


class CarouselImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarouselImage
        fields = [
            "id", "carousel", "image", "link_url",
            "target_type", "target_id", "position", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        carousel = attrs.get("carousel") or getattr(self.instance, "carousel", None)
        if carousel and self.instance is None:
            if carousel.images.count() >= MAX_CAROUSEL_IMAGES:
                raise serializers.ValidationError(
                    f"El carrusel solo permite {MAX_CAROUSEL_IMAGES} imagenes."
                )
        self._validate_dimensions(attrs.get("image"))
        self._validate_target(attrs)
        return attrs

    def _validate_target(self, attrs):
        """
        Reglas del destino del tap:
          - sin tipo -> el id se fuerza a None (banner sin funcion).
          - con tipo -> el id es obligatorio y la entidad debe existir.
        """
        if "target_type" not in attrs and "target_id" not in attrs:
            return  # PATCH que no toca el destino
        target_type = attrs.get(
            "target_type", getattr(self.instance, "target_type", "") or ""
        )
        target_id = attrs.get(
            "target_id", getattr(self.instance, "target_id", None)
        )
        if not target_type:
            attrs["target_type"] = ""
            attrs["target_id"] = None
            return
        if not target_id:
            raise serializers.ValidationError(
                {"target_id": "Requerido cuando el banner tiene un destino."}
            )
        model = _TARGET_MODELS[target_type]
        if not model.objects.filter(pk=target_id).exists():
            raise serializers.ValidationError(
                {"target_id": f"No existe {target_type} con id {target_id}."}
            )
        attrs["target_type"] = target_type
        attrs["target_id"] = target_id

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
    # Estado efectivo (ACTIVE/SCHEDULED/EXPIRED/INACTIVE) segun interruptor + ventana.
    schedule_status = serializers.SerializerMethodField()

    class Meta:
        model = Carousel
        fields = [
            "id",
            "name",
            "width",
            "height",
            "is_active",
            "active_from",
            "active_until",
            "schedule_status",
            "images",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "schedule_status", "created_at", "updated_at"]

    def get_schedule_status(self, obj) -> str:
        return obj.schedule_status()

    def validate(self, attrs):
        start = attrs.get("active_from", getattr(self.instance, "active_from", None))
        end = attrs.get("active_until", getattr(self.instance, "active_until", None))
        if start and end and end <= start:
            raise serializers.ValidationError({
                "active_until": "La fecha de desactivacion debe ser posterior a la de activacion."
            })
        return attrs
