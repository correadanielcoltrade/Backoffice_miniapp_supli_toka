from django.db.models import Count, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.models import Inventory
from apps.orders.models import Order
from apps.payments.models import PaymentTransaction


class SalesSummaryView(APIView):
    """
    Reporte resumen (KPIs) para el dashboard del back office.
    Estructura inicial; los reportes definitivos de posventa estan por confirmar.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=OpenApiTypes.OBJECT,
        description="KPIs para el dashboard: pedidos y pagos por estado, ingresos y bajo stock.",
    )
    def get(self, request):
        orders_by_status = list(
            Order.objects.values("status").annotate(count=Count("id"))
        )
        payments_by_status = list(
            PaymentTransaction.objects.values("status").annotate(count=Count("id"))
        )
        total_paid = (
            Order.objects.filter(status=Order.Status.PAID).aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )
        low_stock = list(
            Inventory.objects.filter(units_in_stock__lte=5)
            .select_related("product")
            .values("product__sku", "product__description", "units_in_stock")[:20]
        )
        return Response(
            {
                "orders_total": Order.objects.count(),
                "orders_by_status": orders_by_status,
                "payments_by_status": payments_by_status,
                "revenue_paid_orders": total_paid,
                "low_stock_products": low_stock,
            }
        )
