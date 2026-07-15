"""
Endpoints 9 y 15 de Wigilabs: Order history y Order detail.

  GET /v1/orders?status=&page=&pageSize=   -> historial paginado del usuario
  GET /v1/orders/{orderId}                 -> detalle de un pedido

Ambos requieren Bearer sessionToken y operan SOLO sobre los pedidos del cliente
autenticado (ownership por sesion). Se listan los pedidos ya realizados (pagados
en adelante), mas recientes primero.
"""
from rest_framework.exceptions import NotFound, ValidationError

from apps.orders.models import Order

from .base import MiniAppAuthView
from .envelope import build_pagination, data_response
from .serializers_order import serialize_order_detail, serialize_order_summary
from .services_payment import (
    DELIVERY_STATUS_TO_ORDER,
    HISTORY_ORDER_STATUSES,
)

_MAX_PAGE_SIZE = 100


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class OrderHistoryView(MiniAppAuthView):
    """Endpoint 9 — GET /v1/orders."""

    def get(self, request):
        p = request.query_params
        qs = (
            request.user.orders
            .prefetch_related("items__product__brand")
            .order_by("-created_at")
        )

        status = p.get("status")
        if status:
            internal = DELIVERY_STATUS_TO_ORDER.get(status)
            if internal is None:
                raise ValidationError({"status": "Use IN_PROGRESS o DELIVERED."})
            qs = qs.filter(status__in=internal)
        else:
            qs = qs.filter(status__in=HISTORY_ORDER_STATUSES)

        total = qs.count()
        page = max(_int(p.get("page"), 1) or 1, 1)
        page_size = min(max(_int(p.get("pageSize"), 10) or 10, 1), _MAX_PAGE_SIZE)
        start = (page - 1) * page_size
        items = qs[start:start + page_size]

        data = [serialize_order_summary(o, request) for o in items]
        return data_response(data, pagination=build_pagination(page, page_size, total))


class OrderDetailView(MiniAppAuthView):
    """Endpoint 15 — GET /v1/orders/{orderId}."""

    def get(self, request, order_id):
        try:
            order = (
                request.user.orders
                .prefetch_related("items__product__brand")
                .get(pk=order_id)
            )
        except (Order.DoesNotExist, ValueError, TypeError):
            raise NotFound("Pedido no encontrado.")
        return data_response(serialize_order_detail(order, request))
