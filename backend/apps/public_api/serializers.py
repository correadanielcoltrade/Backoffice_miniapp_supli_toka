"""
Serializers de la API publica. Exponen SOLO campos seguros para externos:
nada de usuarios, pagos, clientes ni datos personales.
"""
from rest_framework import serializers

from apps.ads.models import Carousel
from apps.catalog.models import Category, Product


class PublicCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class PublicProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    images = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    units_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "description",
            "category",
            "sale_price",
            "images",
            "available",
            "units_in_stock",
        ]

    def get_images(self, obj) -> list[str]:
        request = self.context.get("request")
        urls = []
        for field in ("image1", "image2", "image3", "image4"):
            img = getattr(obj, field)
            if img:
                urls.append(request.build_absolute_uri(img.url) if request else img.url)
        return urls

    def _stock(self, obj):
        inv = getattr(obj, "inventory", None)
        return inv.units_in_stock if inv else 0

    def get_available(self, obj) -> bool:
        return self._stock(obj) > 0

    def get_units_in_stock(self, obj) -> int:
        return self._stock(obj)


class PublicCarouselSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = Carousel
        fields = ["id", "name", "width", "height", "images"]

    def get_images(self, obj) -> list[dict]:
        request = self.context.get("request")
        result = []
        for img in obj.images.all():
            url = img.image.url
            result.append(
                {
                    "url": request.build_absolute_uri(url) if request else url,
                    "position": img.position,
                    "link_url": img.link_url,
                }
            )
        return result
