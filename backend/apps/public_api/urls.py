"""Rutas de la API publica, version 1 (/api/public/v1/)."""
from rest_framework.routers import DefaultRouter

from .views import (
    PublicCarouselViewSet,
    PublicCategoryViewSet,
    PublicProductViewSet,
)

router = DefaultRouter()
router.register(r"products", PublicProductViewSet, basename="public-product")
router.register(r"categories", PublicCategoryViewSet, basename="public-category")
router.register(r"carousels", PublicCarouselViewSet, basename="public-carousel")

urlpatterns = router.urls
