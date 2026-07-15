from django.contrib import admin

from .models import ReturnRequest


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "created_at")
    list_filter = ("status",)
