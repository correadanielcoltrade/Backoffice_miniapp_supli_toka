from rest_framework.routers import DefaultRouter

from .views import ReturnRequestViewSet

router = DefaultRouter()
router.register(r"returns", ReturnRequestViewSet, basename="return")

urlpatterns = router.urls
