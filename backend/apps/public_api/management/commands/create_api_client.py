from django.core.management.base import BaseCommand

from apps.public_api.models import ApiClient


class Command(BaseCommand):
    help = "Crea un consumidor externo y emite su API Key (se muestra una sola vez)."

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Nombre del consumidor externo")
        parser.add_argument("--email", type=str, default="", help="Correo de contacto")
        parser.add_argument(
            "--rate", type=int, default=60, help="Limite de peticiones por minuto"
        )

    def handle(self, *args, **options):
        client, raw_key = ApiClient.issue(
            name=options["name"], contact_email=options["email"]
        )
        if options["rate"] != 60:
            client.rate_limit_per_min = options["rate"]
            client.save(update_fields=["rate_limit_per_min"])

        self.stdout.write(self.style.SUCCESS("Consumidor creado correctamente."))
        self.stdout.write(f"  Nombre : {client.name}")
        self.stdout.write(f"  Limite : {client.rate_limit_per_min}/min")
        self.stdout.write(self.style.WARNING(f"  API Key: {raw_key}"))
        self.stdout.write(
            "  (Copia la API Key ahora; en la base solo se guarda su hash.)"
        )
