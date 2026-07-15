from django.contrib import admin

from .models import Brand, Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name",)
    fields = ("name", "sort_order", "icon", "is_active")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name",)
    fields = ("name", "sort_order", "logo", "is_active")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "description", "category", "brand", "sale_price",
        "is_featured", "is_on_offer", "is_active",
    )
    list_filter = ("category", "brand", "is_active", "is_featured", "is_on_offer")
    search_fields = ("sku", "description")
    fields = (
        "description",
        "long_description",
        "sku",
        "category",
        "brand",
        "sale_price",
        ("image1", "image2"),
        ("image3", "image4"),
        "features",
        "specifications",
        ("is_featured", "is_on_offer", "show_stock"),
        "is_active",
    )
