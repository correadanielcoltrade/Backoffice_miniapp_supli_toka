from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inventory.services import InsufficientStockError, deduct_for_paid_order
from apps.orders.models import Order
from apps.users.models import Role
from apps.users.permissions import HasRole

from .models import PaymentTransaction
from .serializers import (
    PaymentTransactionSerializer,
    TokaPaymentWebhookSerializer,
)


class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Modulo de Seguimiento de Transacciones de Pagos (solo lectura en el back office)."""

    queryset = PaymentTransaction.objects.select_related("order").all()
    serializer_class = PaymentTransactionSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES, Role.LOGISTIC]
    filterset_fields = ["status", "toka_customer_id"]
    search_fields = ["payment_number", "customer_name", "toka_customer_id"]
    ordering_fields = ["created_at", "amount", "status"]


class TokaPaymentWebhookView(APIView):
    """
    Webhook llamado por el BACKEND DE TOKA para confirmar un pago.
    Al confirmarse:
      1. Se registra/actualiza la transaccion de pago.
      2. Si hay pedido asociado, se marca como PAGADO.
      3. Se descuenta el inventario de los productos del pedido (una sola vez).

    Autenticacion: header 'X-Toka-Signature' == TOKA_WEBHOOK_SECRET.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=TokaPaymentWebhookSerializer,
        responses=PaymentTransactionSerializer,
        description="Webhook llamado por el backend de Toka para confirmar un pago.",
    )
    def post(self, request):
        signature = request.headers.get("X-Toka-Signature", "")
        if not settings.TOKA_WEBHOOK_SECRET or signature != settings.TOKA_WEBHOOK_SECRET:
            return Response(
                {"detail": "Firma del webhook invalida."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = TokaPaymentWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            payment, _ = PaymentTransaction.objects.select_for_update().update_or_create(
                payment_number=data["payment_number"],
                defaults={
                    "toka_customer_id": data["toka_customer_id"],
                    "customer_name": data["customer_name"],
                    "amount": data.get("amount"),
                    "status": data["status"],
                    "raw_payload": request.data,
                },
            )

            order = None
            order_id = data.get("order_id")
            if order_id:
                order = Order.objects.select_for_update().filter(pk=order_id).first()
                if order:
                    payment.order = order

            confirmed = data["status"] == PaymentTransaction.Status.CONFIRMED
            if confirmed:
                payment.confirmed_at = timezone.now()

            payment.save()

            # Descontar inventario solo una vez cuando el pago es confirmado
            if confirmed and order and not order.stock_deducted:
                try:
                    deduct_for_paid_order(order, reference=payment.payment_number)
                except InsufficientStockError as exc:
                    return Response(
                        {"detail": str(exc)},
                        status=status.HTTP_409_CONFLICT,
                    )
                order.status = Order.Status.PAID
                order.stock_deducted = True
                order.save(update_fields=["status", "stock_deducted", "updated_at"])

        return Response(
            PaymentTransactionSerializer(payment).data,
            status=status.HTTP_200_OK,
        )
