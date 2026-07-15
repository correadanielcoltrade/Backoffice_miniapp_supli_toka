from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from apps.users.models import Role
from apps.users.permissions import HasRole

from .models import Brand, Category, Product
from .serializers import BrandSerializer, CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.PROCUREMENT]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["is_active"]
    search_fields = ["name"]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.PROCUREMENT]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["is_active"]
    search_fields = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    """Modulo de Gestion de Catalogo."""

    queryset = (
        Product.objects.select_related("category", "brand", "inventory").all()
    )
    serializer_class = ProductSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.PROCUREMENT]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["category", "brand", "is_active", "is_featured", "is_on_offer"]
    search_fields = ["description", "sku"]
    ordering_fields = ["description", "sale_price", "created_at"]
