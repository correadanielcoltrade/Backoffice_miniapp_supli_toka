from rest_framework import serializers

from .models import MAX_CAROUSEL_IMAGES, Carousel, CarouselImage


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
        return attrs


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
