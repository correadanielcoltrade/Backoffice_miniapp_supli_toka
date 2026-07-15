import csv

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.users.models import Role
from apps.users.permissions import HasRole

from .filters import OrderFilter
from .models import Customer, CustomerAddress, Order
from .serializers import (
    CustomerAddressSerializer,
    CustomerSerializer,
    OrderSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.prefetch_related("addresses").all()
    serializer_class = CustomerSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES, Role.LOGISTIC]
    search_fields = ["full_name", "toka_customer_id", "contact_number", "email"]
    ordering_fields = ["full_name", "created_at"]


class CustomerAddressViewSet(viewsets.ModelViewSet):
    """Direcciones guardadas por cliente (tabla independiente por cliente)."""

    queryset = CustomerAddress.objects.select_related("customer").all()
    serializer_class = CustomerAddressSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES, Role.LOGISTIC]
    filterset_fields = ["customer", "is_default"]
    search_fields = ["complete_address", "suburb", "municipality"]


class OrderViewSet(viewsets.ModelViewSet):
    """Modulo de Gestion de Pedidos."""

    queryset = (
        Order.objects.select_related("customer", "saved_address")
        .prefetch_related("items__product")
        .all()
    )
    serializer_class = OrderSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES, Role.LOGISTIC]
    filterset_class = OrderFilter
    search_fields = ["recipient_name", "full_address", "customer__full_name"]
    ordering_fields = ["created_at", "total_amount", "status"]

    @action(detail=False, methods=["get"])
    def export(self, request):
        """
        Descarga en CSV los pedidos que cumplan los filtros aplicados
        (mismos parametros que el listado: created_after, created_before,
        status, customer, search, etc.).
        """
        queryset = self.filter_queryset(self.get_queryset())

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        stamp = timezone.localtime().strftime("%Y%m%d_%H%M")
        response["Content-Disposition"] = (
            f'attachment; filename="pedidos_{stamp}.csv"'
        )
        # BOM para que Excel abra bien los acentos
        response.write("﻿")

        writer = csv.writer(response)
        writer.writerow(
            [
                "#",
                "Cliente",
                "Nombre Completo",
                "Numero de contacto",
                "Direccion Completa",
                "Complemento de direccion",
                "Colonia",
                "Ciudad / Alcaldia",
                "Estado",
                "Codigo postal",
                "Total",
                "Estado del pedido",
                "Fecha de creacion",
            ]
        )
        for o in queryset:
            writer.writerow(
                [
                    o.id,
                    o.customer.full_name,
                    o.recipient_name,
                    o.contact_number,
                    o.full_address,
                    o.address_complement,
                    o.colonia,
                    o.city_alcaldia,
                    o.state,
                    o.postal_code,
                    o.total_amount,
                    o.get_status_display(),
                    timezone.localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
                ]
            )
        return response
