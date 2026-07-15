from django.apps import AppConfig


class MiniappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.miniapp"
    verbose_name = "Mini App BFF (Wigilabs / Supli)"
