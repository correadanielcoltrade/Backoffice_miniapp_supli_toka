"""
Prueba de conexion firmada contra el entorno UAT de Toka.

Hace una llamada REAL y firmada al endpoint de conciliacion
(/v1/acquiring/recon/get) que NO requiere usuario ni appId del mini-program,
por lo que sirve como primer "humo" para validar:
  1) conectividad / TLS con la URL de UAT
  2) que tu Client-Id es valido
  3) que la firma (tus llaves + la llave publica de Toka) esta bien armada

Uso:
    python manage.py test_toka_uat
    python manage.py test_toka_uat --date 2025-07-01
"""
import datetime as dt

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.toka.client import TokaAPIError, TokaClient


class Command(BaseCommand):
    help = "Prueba la conexion firmada con el entorno UAT de Toka."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=(dt.date.today() - dt.timedelta(days=1)).isoformat(),
            help="Fecha de conciliacion YYYY-MM-DD (default: ayer).",
        )
        parser.add_argument(
            "--uri",
            default="/v1/acquiring/recon/get",
            help="Endpoint a probar (default: conciliacion, sin usuario).",
        )

    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING("\n== Prueba de conexion Toka UAT ==\n"))
        self.stdout.write(f"  Entorno   : {settings.TOKA_ENV}")
        self.stdout.write(f"  Base URL  : {settings.TOKA_API_BASE_URL}")
        self.stdout.write(f"  Client-Id : {settings.TOKA_CLIENT_ID or '(vacio!)'}")
        self.stdout.write(f"  Merchant  : {settings.TOKA_MERCHANT_ID or '(vacio)'}")
        self.stdout.write(f"  Endpoint  : {opts['uri']}")
        if not (settings.TOKA_CA_BUNDLE or settings.TOKA_VERIFY_SSL):
            self.stdout.write(self.style.WARNING(
                "  TLS       : verificacion DESACTIVADA (solo UAT)"
            ))
        self.stdout.write("")

        payload = {"reconDate": opts["date"], "settlePeriod": "day"}

        try:
            client = TokaClient()
            resp = client.post(opts["uri"], payload)
        except TokaAPIError as exc:
            self.stdout.write(self.style.ERROR(f"\n[FALLO DE CONFIG/RED] {exc}\n"))
            self.stdout.write(
                "  -> Revisa las rutas de las llaves en .env y la conectividad.\n"
            )
            return

        self.stdout.write(self.style.HTTP_INFO(f"HTTP status: {resp.status_code}"))
        self.stdout.write(f"resultStatus : {resp.result_status}")
        self.stdout.write(f"resultCode   : {resp.result_code}")
        self.stdout.write(f"resultMessage: {resp.result_message}")
        sig_label = "VERIFICADA OK" if resp.signature_ok else "NO verificada"
        style = self.style.SUCCESS if resp.signature_ok else self.style.WARNING
        self.stdout.write("Firma respuesta: " + style(sig_label))
        self.stdout.write("\n--- cuerpo crudo de la respuesta ---")
        self.stdout.write(resp.body_text[:1500] or "(vacio)")
        self.stdout.write("--- fin ---\n")

        self._diagnose(resp)

    def _diagnose(self, resp):
        code = resp.result_code
        if code == "20000004":
            self.stdout.write(self.style.ERROR(
                "\nDIAGNOSTICO: 'The signature is wrong'.\n"
                "  La conectividad esta OK, pero la firma no cuadra. Revisa:\n"
                "   - Que compartiste a Toka la llave PUBLICA correcta (supli_public_key.pem).\n"
                "   - Que TOKA_TOKA_PUBLIC_KEY_PATH apunta a la llave publica que te dio Toka.\n"
                "   - Que el Client-Id es exactamente el que te asignaron.\n"
            ))
        elif code == "20000003":
            self.stdout.write(self.style.ERROR(
                "\nDIAGNOSTICO: 'The client id is invalid'. Revisa TOKA_CLIENT_ID.\n"
            ))
        elif code:
            self.stdout.write(self.style.SUCCESS(
                "\nDIAGNOSTICO: llegaste al servidor y respondio a nivel de negocio.\n"
                "  -> Conexion + Client-Id OK. Si ademas 'Firma respuesta: VERIFICADA OK',\n"
                "     el intercambio de llaves en AMBOS sentidos quedo perfecto.\n"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "\nDIAGNOSTICO: no llego un resultCode estandar. Revisa el cuerpo crudo.\n"
            ))
