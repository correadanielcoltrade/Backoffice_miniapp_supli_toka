import json

from rest_framework import serializers

from .models import Brand, Category, Product


class JSONTextField(serializers.JSONField):
    """
    Acepta tanto JSON nativo (peticiones application/json) como una cadena JSON
    (peticiones multipart/form-data, donde todo llega como texto).
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.strip() == "":
                return []
            try:
                data = json.loads(data)
            except ValueError:
                raise serializers.ValidationError("Formato JSON invalido.")
        return super().to_internal_value(data)


class OptionalPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    """PK opcional: una cadena vacia se interpreta como 'sin valor' (None)."""

    def to_internal_value(self, data):
        if data in ("", None, "null"):
            return None
        return super().to_internal_value(data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "sort_order", "icon", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "sort_order", "logo", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand = OptionalPrimaryKeyField(
        queryset=Brand.objects.all(), required=False, allow_null=True
    )
    brand_name = serializers.SerializerMethodField()
    units_in_stock = serializers.IntegerField(
        source="inventory.units_in_stock", read_only=True
    )
    features = JSONTextField(required=False)
    specifications = JSONTextField(required=False)
    # Lista compacta de las imagenes cargadas (URLs), util para la mini app
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "description",
            "long_description",
            "sku",
            "category",
            "category_name",
            "brand",
            "brand_name",
            "sale_price",
            "units_in_stock",
            "features",
            "specifications",
            "is_featured",
            "is_on_offer",
            "show_stock",
            "image1",
            "image2",
            "image3",
            "image4",
            "images",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "brand_name", "category_name", "units_in_stock",
            "images", "created_at", "updated_at",
        ]

    def get_brand_name(self, obj) -> str:
        return obj.brand.name if obj.brand_id else ""

    def get_images(self, obj) -> list[str]:
        request = self.context.get("request")
        urls = []
        for field in ("image1", "image2", "image3", "image4"):
            img = getattr(obj, field)
            if img:
                urls.append(request.build_absolute_uri(img.url) if request else img.url)
        return urls
