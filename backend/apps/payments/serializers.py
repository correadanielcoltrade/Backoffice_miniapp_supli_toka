from rest_framework import serializers

from .models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "toka_customer_id",
            "customer_name",
            "payment_number",
            "amount",
            "status",
            "status_display",
            "order",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "confirmed_at", "created_at", "updated_at"]


class TokaPaymentWebhookSerializer(serializers.Serializer):
    """Payload esperado desde el backend de Toka al confirmar un pago."""

    toka_customer_id = serializers.CharField()
    customer_name = serializers.CharField()
    payment_number = serializers.CharField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    status = serializers.ChoiceField(
        choices=PaymentTransaction.Status.choices,
        default=PaymentTransaction.Status.CONFIRMED,
    )
    order_id = serializers.IntegerField(required=False, allow_null=True)
