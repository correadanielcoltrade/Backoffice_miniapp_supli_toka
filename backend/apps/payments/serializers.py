from rest_framework import serializers

from .models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    customer_name = serializers.SerializerMethodField()
    order_number = serializers.SerializerMethodField()

    def get_customer_name(self, obj):
        """
        El nombre real del cliente viene del pedido vinculado (recipient_name).
        El snapshot guardado suele ser el id de Toka mientras no tengamos el
        nombre desde la super app (Query User Info). Preferimos el del pedido.
        """
        if obj.order_id and obj.order.recipient_name:
            return obj.order.recipient_name
        return obj.customer_name

    def get_order_number(self, obj):
        """Consecutivo legible del pedido vinculado (SUPLI-000123), si existe."""
        return obj.order.order_number if obj.order_id else None

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "toka_customer_id",
            "customer_name",
            "payment_number",
            "order_number",
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
