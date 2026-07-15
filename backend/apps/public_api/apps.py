from django.apps import AppConfig


class PublicApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.public_api"
    verbose_name = "API Publica (consumidores externos)"

    def ready(self):
        from . import schema  # noqa: F401  (registra el esquema de seguridad)
