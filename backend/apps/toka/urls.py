from django.urls import path

from .views import TokaApplyTokenView, TokaResolveUserView

urlpatterns = [
    # Aislado (util para probar el intercambio de token cuando llegue el appId)
    path("toka/apply-token/", TokaApplyTokenView.as_view(), name="toka-apply-token"),
    # Flujo completo authCode -> 8 campos del pedido (lo usa Pedidos)
    path(
        "toka/order-prefill/",
        TokaResolveUserView.as_view(),
        name="toka-order-prefill",
    ),
]
