import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Filtros del modulo de pedidos, incluyendo rango por fecha de creacion."""

    created_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte", label="Creado desde"
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte", label="Creado hasta"
    )

    class Meta:
        model = Order
        fields = [
            "status",
            "customer",
            "stock_deducted",
            "created_after",
            "created_before",
        ]
