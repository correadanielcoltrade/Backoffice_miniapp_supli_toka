"""
Carga una pequena muestra de codigos postales para poder probar los endpoints
de ubicaciones sin el dataset completo. Para produccion usa `import_sepomex`.

  python manage.py seed_locations
"""
from django.core.management.base import BaseCommand

from apps.locations.models import MexicoPostalCode

# (zip, estado, municipio, ciudad, [colonias])
SAMPLE = [
    ("06000", "Ciudad de Mexico", "Cuauhtemoc", "Ciudad de Mexico", ["Centro"]),
    ("06010", "Ciudad de Mexico", "Cuauhtemoc", "Ciudad de Mexico", ["Centro"]),
    ("03100", "Ciudad de Mexico", "Benito Juarez", "Ciudad de Mexico",
     ["Del Valle Centro", "Del Valle Norte", "Actipan"]),
    ("44100", "Jalisco", "Guadalajara", "Guadalajara",
     ["Centro", "Americana"]),
    ("64000", "Nuevo Leon", "Monterrey", "Monterrey",
     ["Centro", "Maria Luisa"]),
    ("72000", "Puebla", "Puebla", "Puebla", ["Centro"]),
]


class Command(BaseCommand):
    help = "Carga codigos postales de muestra para pruebas."

    def handle(self, *args, **opts):
        created = 0
        for zip_code, state, mnpio, city, suburbs in SAMPLE:
            for suburb in suburbs:
                _, was_created = MexicoPostalCode.objects.get_or_create(
                    zip_code=zip_code,
                    suburb=suburb,
                    defaults={
                        "state": state,
                        "municipality": mnpio,
                        "city": city,
                        "settlement_type": "Colonia",
                    },
                )
                created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f"Muestra cargada. Nuevos registros: {created}.")
        )
