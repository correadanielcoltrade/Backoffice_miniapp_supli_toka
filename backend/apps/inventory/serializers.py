from rest_framework import serializers

from .models import Inventory, StockMovement


class InventorySerializer(serializers.ModelSerializer):
    product_description = serializers.CharField(
        source="product.description", read_only=True
    )
    sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = Inventory
        fields = [
            "id",
            "product",
            "product_description",
            "sku",
            "units_in_stock",
            "reorder_level",
            "updated_at",
        ]
        # units_in_stock y reorder_level son editables; product no.
        read_only_fields = ["id", "product", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    sku = serializers.CharField(source="inventory.product.sku", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "inventory",
            "sku",
            "change",
            "reason",
            "reason_display",
            "reference",
            "created_at",
        ]
        read_only_fields = fields
