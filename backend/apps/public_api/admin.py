from django.contrib import admin, messages

from .models import ApiClient, generate_api_key, hash_key


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "key_prefix",
        "is_active",
        "rate_limit_per_min",
        "last_used_at",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "contact_email", "key_prefix")
    readonly_fields = ("key_prefix", "hashed_key", "last_used_at", "created_at")
    fields = (
        "name",
        "contact_email",
        "is_active",
        "rate_limit_per_min",
        "key_prefix",
        "hashed_key",
        "last_used_at",
        "created_at",
    )
    actions = ["rotate_keys"]

    def save_model(self, request, obj, form, change):
        # Al CREAR un consumidor se genera la clave y se muestra una sola vez.
        if not change:
            raw = generate_api_key()
            obj.key_prefix = raw[:12]
            obj.hashed_key = hash_key(raw)
            super().save_model(request, obj, form, change)
            self.message_user(
                request,
                f"API Key de «{obj.name}» (cópiala ahora, no se vuelve a mostrar): {raw}",
                level=messages.WARNING,
            )
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Rotar API Key (invalida la anterior)")
    def rotate_keys(self, request, queryset):
        for client in queryset:
            raw = client.rotate_key()
            self.message_user(
                request,
                f"Nueva API Key de «{client.name}»: {raw}",
                level=messages.WARNING,
            )
