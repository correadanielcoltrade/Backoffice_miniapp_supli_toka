"""
Rutas del BFF /v1 que consume la mini-app de Wigilabs/Supli.

Se montan bajo /v1/ (ver config/urls.py) para respetar exactamente las rutas
de la especificacion de Wigilabs.
"""
from django.urls import path

from .views_address import AddressDetailView, AddressListCreateView
from .views_auth import AuthSessionView
from .views_catalog import (
    BrandsView,
    CategoriesView,
    ProductDetailView,
    ProductsView,
)
from .views_content import BannersView
from .views_location import (
    LocationByZipView,
    MunicipalitiesView,
    StatesView,
    SuburbsView,
)
from .views_order import OrderDetailView, OrderHistoryView
from .views_payment import CreateOrderView, PaymentStatusView

urlpatterns = [
    # Endpoint 1 - Intercambio de sesion
    path("auth/session", AuthSessionView.as_view(), name="miniapp-auth-session"),
    # Endpoint 2 - createOrder (inicia el pago)
    path(
        "payments/createOrder",
        CreateOrderView.as_view(),
        name="miniapp-create-order",
    ),
    # Endpoint 3 - Banners
    path("content/banners", BannersView.as_view(), name="miniapp-banners"),
    # Endpoint 4 - Categorias
    path("catalog/categories", CategoriesView.as_view(), name="miniapp-categories"),
    # Endpoint 5 - Marcas
    path("catalog/brands", BrandsView.as_view(), name="miniapp-brands"),
    # Endpoints 6 y 7 - Productos (listado / destacados / por ids)
    path("catalog/products", ProductsView.as_view(), name="miniapp-products"),
    # Endpoint 8 - Ficha de producto
    path(
        "catalog/products/<int:product_id>",
        ProductDetailView.as_view(),
        name="miniapp-product-detail",
    ),
    # Endpoints 11 y 13 - Direcciones (listar / crear)
    path(
        "users/me/addresses",
        AddressListCreateView.as_view(),
        name="miniapp-addresses",
    ),
    # Endpoint 12 - Direcciones (editar)
    path(
        "users/me/addresses/<int:address_id>",
        AddressDetailView.as_view(),
        name="miniapp-address-detail",
    ),
    # Endpoint 14 - Catalogo de ubicaciones MX (por CP + cascada)
    path(
        "locations/by-zip-code/<str:zip_code>",
        LocationByZipView.as_view(),
        name="miniapp-location-by-zip",
    ),
    path("locations/states", StatesView.as_view(), name="miniapp-states"),
    path(
        "locations/municipalities",
        MunicipalitiesView.as_view(),
        name="miniapp-municipalities",
    ),
    path("locations/suburbs", SuburbsView.as_view(), name="miniapp-suburbs"),
    # Endpoint 10 - Estado real del pago (mas especifico primero)
    path(
        "orders/<int:order_id>/paymentStatus",
        PaymentStatusView.as_view(),
        name="miniapp-payment-status",
    ),
    # Endpoint 15 - Detalle de un pedido
    path(
        "orders/<int:order_id>",
        OrderDetailView.as_view(),
        name="miniapp-order-detail",
    ),
    # Endpoint 9 - Historial de pedidos
    path("orders", OrderHistoryView.as_view(), name="miniapp-order-history"),
]
