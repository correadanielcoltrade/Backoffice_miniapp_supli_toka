from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.ads.models import Carousel
from apps.catalog.models import Category, Product

from .authentication import ApiKeyAuthentication
from .serializers import (
    PublicCarouselSerializer,
    PublicCategorySerializer,
    PublicProductSerializer,
)
from .throttling import ApiClientRateThrottle


class PublicBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Base de la API publica: solo lectura, autenticada por API Key y con
    throttling por consumidor. No usa JWT ni sesiones del back office.
    """

    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [ApiClientRateThrottle]


class PublicCategoryViewSet(PublicBaseViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = PublicCategorySerializer
    search_fields = ["name"]


class PublicProductViewSet(PublicBaseViewSet):
    """Catalogo de productos activos disponible para consumidores externos."""

    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category", "inventory")
    )
    serializer_class = PublicProductSerializer
    filterset_fields = ["category"]
    search_fields = ["description", "sku"]
    ordering_fields = ["description", "sale_price"]
    lookup_field = "sku"  # /products/<sku>/ es mas estable para externos


class PublicCarouselViewSet(PublicBaseViewSet):
    queryset = (
        Carousel.objects.filter(is_active=True).prefetch_related("images")
    )
    serializer_class = PublicCarouselSerializer
