from django.contrib import admin

from .models import Inventory, StockMovement


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("product", "units_in_stock", "reorder_level", "updated_at")
    search_fields = ("product__sku", "product__description")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("inventory", "change", "reason", "reference", "created_at")
    list_filter = ("reason",)
    search_fields = ("inventory__product__sku", "reference")
