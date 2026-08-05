from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Product

from .models import Customer, CustomerAddress, Order, OrderItem, TrackingEvent


class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = [
            "id",
            "customer",
            "label",
            "custom_label",
            "complete_address",
            "no_street_number",
            "state",
            "municipality",
            "locality",
            "suburb",
            "zip_code",
            "unknown_zip_code",
            "supplementary_address",
            "delivery_instructions",
            "is_default",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CustomerSerializer(serializers.ModelSerializer):
    addresses = CustomerAddressSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "toka_customer_id",
            "full_name",
            "contact_number",
            "email",
            "addresses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_description = serializers.CharField(
        source="product.description", read_only=True
    )
    sku = serializers.CharField(source="product.sku", read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    # Imagenes adjuntas del producto (para el detalle del pedido en el back office).
    images = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "sku",
            "product_description",
            "quantity",
            "unit_price",
            "subtotal",
            "images",
        ]
        read_only_fields = ["id", "unit_price", "subtotal", "images"]

    def get_images(self, obj) -> list[str]:
        request = self.context.get("request")
        urls = []
        for field in ("image1", "image2", "image3", "image4"):
            img = getattr(obj.product, field, None)
            if img:
                urls.append(
                    request.build_absolute_uri(img.url) if request else img.url
                )
        return urls


class TrackingEventSerializer(serializers.ModelSerializer):
    """Un evento del historial de tracking (solo lectura)."""

    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TrackingEvent
        fields = [
            "id", "status", "status_display", "note",
            "created_by_name", "created_at",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj) -> str:
        u = obj.created_by
        return (u.get_full_name() or u.username) if u else ""


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    order_number = serializers.CharField(read_only=True)
    tracking_status_display = serializers.CharField(
        source="get_tracking_status_display", read_only=True
    )
    tracking_events = TrackingEventSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer",
            "customer_name",
            "tracking_status",
            "tracking_status_display",
            "tracking_guide",
            "carrier",
            "tracking_events",
            "saved_address",
            "recipient_name",
            "contact_number",
            "full_address",
            "address_complement",
            "colonia",
            "city_alcaldia",
            "state",
            "postal_code",
            "status",
            "status_display",
            "total_amount",
            "stock_deducted",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_amount",
            "stock_deducted",
            # El tracking se gestiona por la accion dedicada, no por el update.
            "tracking_status",
            "tracking_guide",
            "carrier",
            "created_at",
            "updated_at",
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                product = item["product"]
                OrderItem.objects.create(
                    order=instance,
                    product=product,
                    quantity=item["quantity"],
                    unit_price=product.sale_price,
                )
            instance.recalculate_total()
        return instance


class TrackingUpdateSerializer(serializers.Serializer):
    """
    Entrada de la accion PATCH/POST de tracking: registra un nuevo paso de
    entrega. Solo 'status' es obligatorio; guia/transportadora son opcionales
    y, si vienen, actualizan esos datos del pedido. La 'Novedad' exige nota.
    """

    status = serializers.ChoiceField(choices=Order.DeliveryStatus.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    tracking_guide = serializers.CharField(
        required=False, allow_blank=True, max_length=120
    )
    carrier = serializers.CharField(
        required=False, allow_blank=True, max_length=120
    )

    def validate(self, attrs):
        if attrs["status"] == Order.DeliveryStatus.EXCEPTION and not (
            attrs.get("note") or ""
        ).strip():
            raise serializers.ValidationError(
                {"note": "Describe la Novedad (motivo del incidente)."}
            )
        return attrs
