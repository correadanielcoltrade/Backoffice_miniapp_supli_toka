import django_filters
from django.db.models import Q

from .models import Order


class OrderFilter(django_filters.FilterSet):
    """
    Filtros del modulo de pedidos: rango por fecha, estado de entrega (tracking)
    y una busqueda libre (q) que abarca # de pedido, cliente, destinatario, etc.
    """

    created_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte", label="Creado desde"
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte", label="Creado hasta"
    )
    tracking_status = django_filters.ChoiceFilter(
        field_name="tracking_status",
        choices=Order.DeliveryStatus.choices,
        label="Estado de entrega",
    )
    q = django_filters.CharFilter(method="filter_q", label="Busqueda")

    class Meta:
        model = Order
        fields = [
            "status",
            "customer",
            "stock_deducted",
            "created_after",
            "created_before",
            "tracking_status",
            "q",
        ]

    def filter_q(self, queryset, name, value):
        """
        Busqueda libre: # de pedido (SUPLI-000019 / 000019 / 19), cliente
        (nombre o id de Toka), destinatario, direccion, colonia o guia.
        """
        value = (value or "").strip()
        if not value:
            return queryset
        cond = (
            Q(recipient_name__icontains=value)
            | Q(customer__full_name__icontains=value)
            | Q(customer__toka_customer_id__icontains=value)
            | Q(full_address__icontains=value)
            | Q(colonia__icontains=value)
            | Q(tracking_guide__icontains=value)
        )
        # # de pedido: se normaliza quitando el prefijo SUPLI- y ceros -> id.
        normalized = value.upper().replace("SUPLI", "").replace("-", "").strip()
        if normalized.isdigit() and len(normalized) <= 9:
            cond |= Q(id=int(normalized))
        return queryset.filter(cond)
