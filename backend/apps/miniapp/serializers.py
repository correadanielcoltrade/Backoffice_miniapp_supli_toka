"""
Serializers del BFF /v1. Traducen los modelos internos (snake_case) a la forma
EXACTA que pide Wigilabs (camelCase). Los modelos NO se renombran: el mapeo se
hace aqui, en la capa de presentacion.
"""
from rest_framework import serializers

CURRENCY = "MXN"


def _abs_url(request, filefield):
    if not filefield:
        return None
    return request.build_absolute_uri(filefield.url) if request else filefield.url


def _first_image(request, product):
    for field in ("image1", "image2", "image3", "image4"):
        img = getattr(product, field, None)
        if img:
            return _abs_url(request, img)
    return None


def _all_images(request, product):
    urls = []
    for field in ("image1", "image2", "image3", "image4"):
        img = getattr(product, field, None)
        if img:
            urls.append(_abs_url(request, img))
    return urls


def _stock(product):
    inv = getattr(product, "inventory", None)
    return inv.units_in_stock if inv else 0


def _price(product):
    return {"value": str(product.sale_price), "currency": CURRENCY}


class BannerSerializer(serializers.Serializer):
    """Endpoint 3: { bannerId, sortOrder, linkUrl, imageUrl }."""

    bannerId = serializers.IntegerField(source="id")
    sortOrder = serializers.IntegerField(source="position")
    linkUrl = serializers.CharField(source="link_url", allow_blank=True)
    imageUrl = serializers.SerializerMethodField()

    def get_imageUrl(self, obj):
        return _abs_url(self.context.get("request"), obj.image)


class CategorySerializer(serializers.Serializer):
    """Endpoint 4: { categoryId, sortOrder, name, iconUrl }."""

    categoryId = serializers.IntegerField(source="id")
    sortOrder = serializers.IntegerField(source="sort_order")
    name = serializers.CharField()
    iconUrl = serializers.SerializerMethodField()

    def get_iconUrl(self, obj):
        return _abs_url(self.context.get("request"), obj.icon)


class BrandSerializer(serializers.Serializer):
    """Endpoint 5: { brandId, sortOrder, name, logoUrl }."""

    brandId = serializers.IntegerField(source="id")
    sortOrder = serializers.IntegerField(source="sort_order")
    name = serializers.CharField()
    logoUrl = serializers.SerializerMethodField()

    def get_logoUrl(self, obj):
        return _abs_url(self.context.get("request"), obj.logo)


class ProductListSerializer(serializers.Serializer):
    """
    Endpoints 6 y 7 (listado / destacados):
    { productId, name, brandName, imageUrl, price{value,currency},
      stockAvailable, showStock }.
    """

    productId = serializers.IntegerField(source="id")
    name = serializers.CharField(source="description")
    brandName = serializers.SerializerMethodField()
    imageUrl = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    stockAvailable = serializers.SerializerMethodField()
    showStock = serializers.BooleanField(source="show_stock")

    def get_brandName(self, obj):
        return obj.brand.name if obj.brand_id else ""

    def get_imageUrl(self, obj):
        return _first_image(self.context.get("request"), obj)

    def get_price(self, obj):
        return _price(obj)

    def get_stockAvailable(self, obj):
        return _stock(obj)


class ProductDetailSerializer(serializers.Serializer):
    """
    Endpoint 8 (ficha). Como NO manejamos variantes (1 producto = 1 SKU),
    se devuelve una variante degenerada con productIdVariant == productId,
    para que el contrato del front (que usa productIdVariant) siga funcionando.
    """

    productId = serializers.IntegerField(source="id")
    name = serializers.CharField(source="description")
    brand = serializers.SerializerMethodField()
    description = serializers.CharField(source="long_description", allow_blank=True)
    features = serializers.JSONField()
    specifications = serializers.JSONField()
    price = serializers.SerializerMethodField()
    stockAvailable = serializers.SerializerMethodField()
    showStock = serializers.BooleanField(source="show_stock")
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    def get_brand(self, obj):
        return obj.brand.name if obj.brand_id else ""

    def get_price(self, obj):
        return _price(obj)

    def get_stockAvailable(self, obj):
        return _stock(obj)

    def get_images(self, obj):
        return _all_images(self.context.get("request"), obj)

    def get_variants(self, obj):
        request = self.context.get("request")
        return [{
            "productIdVariant": obj.id,
            "sku": obj.sku,
            "attributes": {},
            "images": _all_images(request, obj),
            "price": _price(obj),
            "stockAvailable": _stock(obj),
            "showStock": obj.show_stock,
        }]
