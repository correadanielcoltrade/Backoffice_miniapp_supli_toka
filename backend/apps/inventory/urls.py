from rest_framework.routers import DefaultRouter

from .views import InventoryViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r"inventory", InventoryViewSet, basename="inventory")
router.register(r"stock-movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls
