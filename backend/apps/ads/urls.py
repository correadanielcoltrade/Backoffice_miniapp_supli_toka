from rest_framework.routers import DefaultRouter

from .views import CarouselImageViewSet, CarouselViewSet

router = DefaultRouter()
router.register(r"carousels", CarouselViewSet, basename="carousel")
router.register(r"carousel-images", CarouselImageViewSet, basename="carousel-image")

urlpatterns = router.urls
