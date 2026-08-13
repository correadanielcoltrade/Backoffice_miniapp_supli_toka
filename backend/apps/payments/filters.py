import django_filters

from .models import PaymentTransaction


class PaymentFilter(django_filters.FilterSet):
    """Filtros del modulo de pagos: estado, cliente y rango por fecha de creacion."""

    created_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte", label="Creado desde"
    )
    created_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte", label="Creado hasta"
    )

    class Meta:
        model = PaymentTransaction
        fields = [
            "status",
            "toka_customer_id",
            "created_after",
            "created_before",
        ]
