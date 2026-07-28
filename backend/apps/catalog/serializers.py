import json

from rest_framework import serializers

from .models import (
    BRAND_LOGO_MAX_HEIGHT,
    BRAND_LOGO_WIDTH,
    CATEGORY_ICON_HEIGHT,
    CATEGORY_ICON_WIDTH,
    PRODUCT_IMAGE_HEIGHT,
    PRODUCT_IMAGE_WIDTH,
    Brand,
    Category,
    Product,
)


def _image_size(image):
    """
    Devuelve (ancho, alto) de un archivo de imagen subido. Reutiliza la
    instancia Pillow que el ImageField ya abrio al validar; si no esta
    disponible, abre el archivo y deja el puntero en 0.
    """
    pil = getattr(image, "image", None)
    if pil is not None:
        return pil.size
    from PIL import Image

    image.seek(0)
    with Image.open(image) as img:
        size = img.size
    image.seek(0)
    return size


def validate_exact_dimensions(image, field, label, exp_width, exp_height):
    """Exige que la imagen mida EXACTAMENTE exp_width x exp_height px."""
    if image is None:
        return
    width, height = _image_size(image)
    if (width, height) != (exp_width, exp_height):
        raise serializers.ValidationError({
            field: (
                f"{label} debe medir exactamente {exp_width}x{exp_height} px. "
                f"La imagen que subiste mide {width}x{height} px."
            )
        })


def validate_logo_dimensions(image, field="logo"):
    """
    Logo de marca: ancho EXACTO (BRAND_LOGO_WIDTH) y alto variable segun el
    aspecto real del logo, sin superar BRAND_LOGO_MAX_HEIGHT px.
    """
    if image is None:
        return
    width, height = _image_size(image)
    if width != BRAND_LOGO_WIDTH or height > BRAND_LOGO_MAX_HEIGHT:
        raise serializers.ValidationError({
            field: (
                f"El logo debe medir {BRAND_LOGO_WIDTH} px de ancho y hasta "
                f"{BRAND_LOGO_MAX_HEIGHT} px de alto. La imagen que subiste mide "
                f"{width}x{height} px."
            )
        })


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

    def validate(self, attrs):
        # En un PATCH sin icono nuevo, attrs["icon"] no viene y no se valida.
        validate_exact_dimensions(
            attrs.get("icon"), "icon", "El icono de la categoria",
            CATEGORY_ICON_WIDTH, CATEGORY_ICON_HEIGHT,
        )
        return attrs


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "sort_order", "logo", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        validate_logo_dimensions(attrs.get("logo"))
        return attrs


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

    def validate(self, attrs):
        # Cada una de las 4 imagenes (las que vengan en esta peticion) debe ser
        # un cuadrado exacto PRODUCT_IMAGE_WIDTH x PRODUCT_IMAGE_HEIGHT.
        for i in (1, 2, 3, 4):
            field = f"image{i}"
            validate_exact_dimensions(
                attrs.get(field), field, f"La imagen {i} del producto",
                PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT,
            )
        return attrs

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
