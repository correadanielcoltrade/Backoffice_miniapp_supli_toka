from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Product

from .models import Customer, CustomerAddress, Order, OrderItem


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
        ]
        read_only_fields = ["id", "unit_price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "customer_name",
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
            "created_at",
            "updated_at",
        ]

    def _prefill_address_from_saved(self, validated_data):
        """Si se selecciona una direccion guardada y no se envian los campos,
        se copian (en formato MX) como snapshot editable del pedido."""
        saved = validated_data.get("saved_address")
        if saved:
            defaults = {
                "full_address": saved.complete_address,
                "address_complement": saved.supplementary_address,
                "colonia": saved.suburb,
                "city_alcaldia": saved.municipality,
                "state": saved.state,
                "postal_code": saved.zip_code,
            }
            for field, value in defaults.items():
                validated_data.setdefault(field, value)

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        self._prefill_address_from_saved(validated_data)
        order = Order.objects.create(**validated_data)
        for item in items_data:
            product = item["product"]
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                unit_price=product.sale_price,
            )
        order.recalculate_total()
        return order

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
