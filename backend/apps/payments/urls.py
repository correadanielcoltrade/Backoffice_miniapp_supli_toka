from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PaymentTransactionViewSet, TokaPaymentWebhookView

router = DefaultRouter()
router.register(r"payments", PaymentTransactionViewSet, basename="payment")

urlpatterns = router.urls + [
    path(
        "webhooks/toka/payment/",
        TokaPaymentWebhookView.as_view(),
        name="toka-payment-webhook",
    ),
]
