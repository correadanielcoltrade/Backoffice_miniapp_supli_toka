"""
Emite un sessionToken de PRUEBA para desarrollo, SIN pasar por Toka.

El endpoint POST /v1/auth/session depende de Toka (applyToken + inquiryUserInfo)
y del appId, por lo que no se puede ejercitar en local hasta tener esos insumos.
Este comando crea (o reutiliza) un Customer de prueba y firma un sessionToken
valido para poder probar los endpoints /v1 autenticados (catalogo, direcciones,
ordenes) mientras tanto. NO usar en produccion.

Uso:
  python manage.py issue_test_session
  python manage.py issue_test_session --name "QA Wigilabs" --toka-id TEST-WIGILABS
"""
from django.core.management.base import BaseCommand

from apps.miniapp.authentication import issue_session_token
from apps.orders.models import Customer


class Command(BaseCommand):
    help = "Emite un sessionToken de prueba (dev) sin pasar por Toka."

    def add_arguments(self, parser):
        parser.add_argument("--toka-id", default="TEST-LOCAL",
                            help="toka_customer_id del cliente de prueba.")
        parser.add_argument("--name", default="Usuario de Prueba")
        parser.add_argument("--email", default="qa@supli.tech")

    def handle(self, *args, **opts):
        customer, created = Customer.objects.get_or_create(
            toka_customer_id=opts["toka_id"],
            defaults={"full_name": opts["name"], "email": opts["email"]},
        )
        token, expires_in = issue_session_token(customer)

        estado = "creado" if created else "reutilizado"
        self.stdout.write(self.style.SUCCESS(
            f"Customer de prueba {estado}: id={customer.id} "
            f"toka_id={customer.toka_customer_id}"
        ))
        self.stdout.write("")
        self.stdout.write(f"sessionToken (valido ~{expires_in // 60} min):")
        self.stdout.write(token)
        self.stdout.write("")
        self.stdout.write("Prueba rapida:")
        self.stdout.write(
            '  curl http://127.0.0.1:8000/v1/catalog/categories '
            f'-H "Authorization: Bearer {token}"'
        )
