"""
Sube a Cloudflare R2 las imagenes que ya estan guardadas en el disco local
(MEDIA_ROOT) y que fueron cargadas antes de activar R2.

Recorre todos los modelos con ImageField/FileField (banners del carrusel,
iconos de categorias, logos de marcas e imagenes de productos), y por cada
archivo que exista en local pero NO en R2, lo sube conservando su ruta
(upload_to). No modifica la base de datos: el name del campo no cambia, solo
cambia el storage donde vive el archivo.

Uso:
    python manage.py migrate_media_to_r2            # sube lo que falte
    python manage.py migrate_media_to_r2 --dry-run  # solo muestra que haria
    python manage.py migrate_media_to_r2 --overwrite # re-sube aunque ya exista
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from django.db.models import FileField


class Command(BaseCommand):
    help = "Sube las imagenes locales (MEDIA_ROOT) al bucket de Cloudflare R2."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que archivos se subirian, sin subir nada.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Re-sube el archivo aunque ya exista en R2.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_R2", False):
            raise CommandError(
                "USE_R2 esta en False. Activalo en .env para migrar a R2."
            )

        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        # Storage destino (R2) = el 'default' actual.
        remote = storages["default"]
        media_root = Path(settings.MEDIA_ROOT)

        uploaded = skipped = missing = 0

        for model in apps.get_models():
            file_fields = [
                f.name
                for f in model._meta.get_fields()
                if isinstance(f, FileField)
            ]
            if not file_fields:
                continue

            for obj in model.objects.all().iterator():
                for field_name in file_fields:
                    field_file = getattr(obj, field_name)
                    if not field_file:  # campo vacio
                        continue

                    name = field_file.name  # ruta relativa, ej ads/carousel/x.png
                    local_path = media_root / name

                    if not local_path.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [FALTA LOCAL] {model.__name__}.{field_name} "
                                f"-> {name} (no esta en disco, se omite)"
                            )
                        )
                        missing += 1
                        continue

                    if remote.exists(name) and not overwrite:
                        skipped += 1
                        continue

                    label = f"{model.__name__}.{field_name} -> {name}"
                    if dry_run:
                        self.stdout.write(f"  [SUBIRIA] {label}")
                        uploaded += 1
                        continue

                    with local_path.open("rb") as fh:
                        # save() respeta el 'name' exacto (mismo path que la BD).
                        remote.save(name, fh)
                    self.stdout.write(self.style.SUCCESS(f"  [OK] {label}"))
                    uploaded += 1

        resumen = (
            f"\nResumen: {uploaded} subidas, {skipped} ya existian, "
            f"{missing} sin archivo local."
        )
        if dry_run:
            resumen = f"\n(DRY-RUN) {uploaded} se subirian, {skipped} ya existen."
        self.stdout.write(self.style.SUCCESS(resumen))
