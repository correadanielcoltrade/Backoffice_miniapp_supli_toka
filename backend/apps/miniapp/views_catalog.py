"""
Endpoints 4-8 de Wigilabs: categorias, marcas, productos (listado / destacados /
por ids) y ficha de producto.
"""
from django.db.models import Q
from rest_framework.exceptions import NotFound

from apps.catalog.models import Brand, Category, Product

from .base import MiniAppFlexibleAuthView
from .envelope import build_pagination, data_response
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

_SORTS = {
    "price_asc": "sale_price",
    "price_desc": "-sale_price",
    "name_asc": "description",
    "name_desc": "-description",
    "newest": "-created_at",
    "oldest": "created_at",
}
_DEFAULT_SORT = "-created_at"
_MAX_PAGE_SIZE = 100


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _truthy(value):
    return str(value).lower() in ("1", "true", "yes")


class CategoriesView(MiniAppFlexibleAuthView):
    """GET /v1/catalog/categories."""

    def get(self, request):
        qs = Category.objects.filter(is_active=True)
        data = CategorySerializer(qs, many=True, context={"request": request}).data
        return data_response(data)


class BrandsView(MiniAppFlexibleAuthView):
    """GET /v1/catalog/brands."""

    def get(self, request):
        qs = Brand.objects.filter(is_active=True)
        data = BrandSerializer(qs, many=True, context={"request": request}).data
        return data_response(data)


class ProductsView(MiniAppFlexibleAuthView):
    """
    GET /v1/catalog/products
    Filtros: featured, offer, categoryId, brandId, search, ids (lote), sort.
    Paginacion: page, pageSize.
    """

    def get(self, request):
        p = request.query_params
        qs = (
            Product.objects.filter(is_active=True)
            .select_related("brand", "category", "inventory")
        )

        ids = p.get("ids")
        if ids:
            id_list = [i for i in (_int(x) for x in ids.split(",")) if i is not None]
            qs = qs.filter(id__in=id_list)
        if _truthy(p.get("featured")):
            qs = qs.filter(is_featured=True)
        if _truthy(p.get("offer")):
            qs = qs.filter(is_on_offer=True)
        category_id = _int(p.get("categoryId"))
        if category_id:
            qs = qs.filter(category_id=category_id)
        brand_id = _int(p.get("brandId"))
        if brand_id:
            qs = qs.filter(brand_id=brand_id)
        search = p.get("search") or p.get("q")
        if search:
            qs = qs.filter(Q(description__icontains=search) | Q(sku__icontains=search))

        sort_key = (p.get("sort") or "").lower()
        qs = qs.order_by(_SORTS.get(sort_key, _DEFAULT_SORT))

        total = qs.count()
        page = max(_int(p.get("page"), 1) or 1, 1)
        page_size = min(max(_int(p.get("pageSize"), 20) or 20, 1), _MAX_PAGE_SIZE)
        start = (page - 1) * page_size
        items = qs[start:start + page_size]

        data = ProductListSerializer(
            items, many=True, context={"request": request}
        ).data
        return data_response(
            data, pagination=build_pagination(page, page_size, total)
        )


class ProductDetailView(MiniAppFlexibleAuthView):
    """GET /v1/catalog/products/{productId}."""

    def get(self, request, product_id):
        try:
            product = (
                Product.objects
                .select_related("brand", "category", "inventory")
                .get(id=product_id, is_active=True)
            )
        except Product.DoesNotExist:
            raise NotFound("Producto no encontrado.")
        data = ProductDetailSerializer(product, context={"request": request}).data
        return data_response(data)
