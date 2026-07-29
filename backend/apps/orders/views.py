from io import BytesIO

import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
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
        Descarga en Excel (.xlsx) los pedidos que cumplan los filtros aplicados
        (mismos parametros que el listado: created_after, created_before,
        status, customer, search, etc.).

        Formato picking: UNA FILA POR PRODUCTO. Los datos del pedido se repiten
        en cada fila de sus productos, para poder filtrar/sumar por SKU y
        despachar comodamente en Excel.
        """
        queryset = self.filter_queryset(self.get_queryset())

        headers = [
            "N° Pedido",
            "Cliente",
            "Nombre Completo",
            "Numero de contacto",
            "Direccion Completa",
            "Complemento de direccion",
            "Colonia",
            "Ciudad / Alcaldia",
            "Estado",
            "Codigo postal",
            "Producto",
            "SKU",
            "Cantidad",
            "Precio unitario",
            "Subtotal",
            "Total del pedido",
            "Estado del pedido",
            "Fecha de creacion",
        ]
        # Columnas con formato de moneda (1-indexado, para openpyxl).
        money_cols = {14, 15, 16}  # Precio unitario, Subtotal, Total del pedido
        qty_col = 13

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pedidos"

        header_fill = PatternFill("solid", fgColor="1F3B57")
        header_font = Font(bold=True, color="FFFFFF")
        ws.append(headers)
        for col, _ in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(vertical="center")

        def order_base(o):
            return [
                o.order_number,
                o.customer.full_name,
                o.recipient_name,
                o.contact_number,
                o.full_address,
                o.address_complement,
                o.colonia,
                o.city_alcaldia,
                o.state,
                o.postal_code,
            ]

        def order_tail(o):
            return [
                float(o.total_amount),
                o.get_status_display(),
                timezone.localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
            ]

        for o in queryset:
            items = list(o.items.all())
            if items:
                for it in items:
                    ws.append(
                        order_base(o)
                        + [
                            it.product.description,
                            it.product.sku,
                            it.quantity,
                            float(it.unit_price),
                            float(it.subtotal),
                        ]
                        + order_tail(o)
                    )
            else:
                # Pedido sin productos: una fila con las columnas de producto vacias.
                ws.append(order_base(o) + ["", "", "", "", ""] + order_tail(o))

        # Formato de moneda y cantidad para las filas de datos.
        for row in range(2, ws.max_row + 1):
            for col in money_cols:
                ws.cell(row=row, column=col).number_format = '"$"#,##0.00'
            ws.cell(row=row, column=qty_col).alignment = Alignment(
                horizontal="center"
            )

        # Anchos de columna aproximados para que se lea bien de una.
        widths = [14, 22, 22, 16, 30, 22, 18, 20, 16, 12, 28, 16, 10, 15, 13, 15, 18, 18]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

        # Fila de encabezados fija + autofiltro para ordenar/filtrar en Excel.
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{ws.max_row}"

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        stamp = timezone.localtime().strftime("%Y%m%d_%H%M")
        response = HttpResponse(
            buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = (
            f'attachment; filename="pedidos_{stamp}.xlsx"'
        )
        return response
