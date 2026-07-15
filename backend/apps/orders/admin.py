from django.contrib import admin

from .models import Customer, CustomerAddress, Order, OrderItem


class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "toka_customer_id", "contact_number", "email")
    search_fields = ("full_name", "toka_customer_id", "contact_number")
    inlines = [CustomerAddressInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "status",
        "total_amount",
        "stock_deducted",
        "created_at",
    )
    list_filter = ("status", "stock_deducted")
    search_fields = ("recipient_name", "customer__full_name", "full_address")
    inlines = [OrderItemInline]


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = (
        "customer", "label", "complete_address", "suburb", "municipality",
        "state", "is_default",
    )
    list_filter = ("label", "state")
    search_fields = ("customer__full_name", "complete_address", "suburb")
