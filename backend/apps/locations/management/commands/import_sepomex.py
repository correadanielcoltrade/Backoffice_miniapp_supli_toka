"""
Importa el catalogo postal oficial de SEPOMEX a MexicoPostalCode.

El archivo oficial ("CPdescarga.txt") se descarga de:
  https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/CodigoPostal_Exportar.aspx
Es un TXT delimitado por '|', codificado en latin-1, con una primera linea de
aviso y una segunda linea de encabezados. Columnas relevantes:
  d_codigo | d_asenta | d_tipo_asenta | D_mnpio | d_estado | d_ciudad | ...

Uso:
  python manage.py import_sepomex "C:/ruta/CPdescarga.txt"
  python manage.py import_sepomex "C:/ruta/CPdescarga.txt" --replace
"""
import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.locations.models import MexicoPostalCode

BATCH = 5000


class Command(BaseCommand):
    help = "Importa el catalogo postal de SEPOMEX (archivo CPdescarga.txt)."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Ruta al archivo CPdescarga.txt de SEPOMEX.")
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Vacia la tabla antes de importar.",
        )
        parser.add_argument(
            "--encoding",
            default="latin-1",
            help="Codificacion del archivo (por defecto latin-1).",
        )

    def handle(self, *args, **opts):
        path = opts["path"]
        try:
            fh = open(path, encoding=opts["encoding"])
        except OSError as exc:
            raise CommandError(f"No se pudo abrir el archivo: {exc}")

        with fh:
            lines = fh.read().splitlines()

        # La 1a linea es un aviso; la 2a son los encabezados.
        if len(lines) < 3:
            raise CommandError("El archivo no tiene el formato esperado de SEPOMEX.")
        header = lines[1].split("|")
        try:
            idx = {
                "zip": header.index("d_codigo"),
                "suburb": header.index("d_asenta"),
                "type": header.index("d_tipo_asenta"),
                "mnpio": header.index("D_mnpio"),
                "state": header.index("d_estado"),
                "city": header.index("d_ciudad"),
            }
        except ValueError as exc:
            raise CommandError(f"Encabezado inesperado: {exc}")

        if opts["replace"]:
            self.stdout.write("Vaciando la tabla actual…")
            MexicoPostalCode.objects.all().delete()

        reader = csv.reader(lines[2:], delimiter="|")
        buffer, total = [], 0
        for row in reader:
            if not row or len(row) <= idx["state"]:
                continue
            buffer.append(
                MexicoPostalCode(
                    zip_code=row[idx["zip"]].strip(),
                    suburb=row[idx["suburb"]].strip(),
                    settlement_type=row[idx["type"]].strip(),
                    municipality=row[idx["mnpio"]].strip(),
                    state=row[idx["state"]].strip(),
                    city=row[idx["city"]].strip(),
                )
            )
            if len(buffer) >= BATCH:
                with transaction.atomic():
                    MexicoPostalCode.objects.bulk_create(buffer)
                total += len(buffer)
                buffer = []
                self.stdout.write(f"  {total} filas…")
        if buffer:
            with transaction.atomic():
                MexicoPostalCode.objects.bulk_create(buffer)
            total += len(buffer)

        self.stdout.write(self.style.SUCCESS(f"Importadas {total} filas de SEPOMEX."))
