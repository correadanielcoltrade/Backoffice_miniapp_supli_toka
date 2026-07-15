"""
Prueba del flujo de usuario de Toka: authCode -> Apply Token -> Query User Info.

Requiere que Toka ya haya entregado el appId (TOKA_APP_ID en .env) y un authCode
real generado por el JSAPI del mini-program.

Uso:
    python manage.py test_toka_user --auth-code XXXXXX
"""
from django.core.management.base import BaseCommand, CommandError

from apps.toka.client import TokaAPIError, TokaClient
from apps.toka.views import map_user_info_to_prefill


class Command(BaseCommand):
    help = "Prueba Apply Token + Query User Info con un authCode real."

    def add_arguments(self, parser):
        parser.add_argument("--auth-code", required=True, help="authCode del JSAPI.")

    def handle(self, *args, **opts):
        client = TokaClient()

        self.stdout.write(self.style.MIGRATE_HEADING("\n== 1) Apply Token ==\n"))
        try:
            token = client.apply_token(auth_code=opts["auth_code"])
        except TokaAPIError as exc:
            raise CommandError(str(exc))

        self.stdout.write(f"  resultCode : {token.result_code} {token.result_message}")
        self.stdout.write(f"  firma resp : {'OK' if token.signature_ok else 'NO'}")
        if token.result_status != "S":
            raise CommandError("Apply Token fallo. Revisa el authCode / appId.")
        access_token = token.data.get("accessToken")
        self.stdout.write(f"  userId     : {token.data.get('userId')}")
        self.stdout.write(f"  accessToken: {(access_token or '')[:40]}...")

        self.stdout.write(self.style.MIGRATE_HEADING("\n== 2) Query User Info ==\n"))
        try:
            info = client.query_user_info(access_token)
        except TokaAPIError as exc:
            raise CommandError(str(exc))

        self.stdout.write(f"  resultCode : {info.result_code} {info.result_message}")
        self.stdout.write(f"  firma resp : {'OK' if info.signature_ok else 'NO'}")
        if info.result_status != "S":
            raise CommandError("Query User Info fallo.")

        self.stdout.write(self.style.MIGRATE_HEADING("\n== 3) Mapeo a los 8 campos ==\n"))
        prefill = map_user_info_to_prefill(info.data)
        for k, v in prefill.items():
            self.stdout.write(f"  {k:20}: {v}")
        self.stdout.write(self.style.SUCCESS("\nFlujo de usuario COMPLETO.\n"))
