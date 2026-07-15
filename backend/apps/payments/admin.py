from django.contrib import admin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number",
        "toka_customer_id",
        "customer_name",
        "amount",
        "status",
        "order",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("payment_number", "customer_name", "toka_customer_id")
