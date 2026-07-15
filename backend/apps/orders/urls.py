from rest_framework.routers import DefaultRouter

from .views import CustomerAddressViewSet, CustomerViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"customer-addresses", CustomerAddressViewSet, basename="customer-address")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = router.urls
