"""
Importa productos al catalogo desde un CSV (la "Plantilla de Productos").

Formato del CSV (delimitador ';', UTF-8):
  Nombre; SKU; Categoria; Marca; Precio de venta MXN; Descripcion Larga;
  Caracteristicas; Especificaciones; Imagen url 1..4

- Precio en formato MX ("335,31" = 335.31). Se usa ',' como decimal.
- Caracteristicas: una por linea -> lista de strings (features).
- Especificaciones: una "clave: valor" por linea -> [{key, value}] (specifications).
- Imagenes: se recibe la URL publica de R2; se guarda solo la KEY (ruta dentro
  del bucket) para que ImageField reconstruya la .url. No se re-suben archivos.
- Categoria y Marca se crean si no existen (get_or_create por nombre).
- Idempotente: update_or_create por SKU (re-ejecutar actualiza, no duplica).

Uso:
    python manage.py import_products "ruta/al/archivo.csv" --dry-run
    python manage.py import_products "ruta/al/archivo.csv"
"""
import csv
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Brand, Category, Product

# Orden de columnas en la plantilla (por indice, robusto ante acentos del header).
COL_NAME, COL_SKU, COL_CATEGORY, COL_BRAND, COL_PRICE = 0, 1, 2, 3, 4
COL_LONG_DESC, COL_FEATURES, COL_SPECS = 5, 6, 7
COL_IMAGES = (8, 9, 10, 11)


def parse_price(raw):
    """'335,31' -> Decimal('335.31'). MX: '.' miles, ',' decimal."""
    s = (raw or "").strip().replace(" ", "")
    if not s:
        raise ValueError("precio vacio")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"precio invalido: {raw!r}")


def parse_features(raw):
    """Una caracteristica por linea -> lista de strings."""
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def parse_specs(raw):
    """'clave: valor' por linea -> [{'key':..., 'value':...}]."""
    specs = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            specs.append({"key": key.strip(), "value": value.strip()})
        else:
            specs.append({"key": line, "value": ""})
    return specs


def url_to_key(url):
    """URL publica de R2 -> key dentro del bucket. Vacio -> None."""
    url = (url or "").strip()
    if not url:
        return None
    parsed = urlparse(url)
    # Si es URL absoluta usa el path; si ya es una ruta relativa, usala tal cual.
    path = parsed.path if parsed.scheme else url
    return path.lstrip("/")


class Command(BaseCommand):
    help = "Importa productos al catalogo desde la Plantilla de Productos (CSV)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta al archivo CSV.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra lo que haria, sin escribir en la base.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]

        try:
            fh = open(csv_path, encoding="utf-8-sig", newline="")
        except OSError as exc:
            raise CommandError(f"No se pudo abrir el CSV: {exc}")

        with fh:
            rows = list(csv.reader(fh, delimiter=";"))

        if len(rows) < 2:
            raise CommandError("El CSV no tiene filas de datos.")

        data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]
        self.stdout.write(
            f"{'(DRY-RUN) ' if dry_run else ''}Filas de datos: {len(data_rows)}\n"
        )

        created = updated = 0
        errores = []

        # No abrimos transaccion en dry-run (no escribimos nada).
        ctx = transaction.atomic() if not dry_run else _NullCtx()
        with ctx:
            for i, row in enumerate(data_rows, start=2):  # fila 1 = header
                try:
                    name = row[COL_NAME].strip()
                    sku = row[COL_SKU].strip()
                    if not sku:
                        raise ValueError("SKU vacio")
                    cat_name = row[COL_CATEGORY].strip() or "Sin categoria"
                    brand_name = row[COL_BRAND].strip()
                    price = parse_price(row[COL_PRICE])
                    long_desc = row[COL_LONG_DESC].strip()
                    features = parse_features(row[COL_FEATURES])
                    specs = parse_specs(row[COL_SPECS])
                    image_keys = [url_to_key(row[c]) for c in COL_IMAGES]

                    if dry_run:
                        imgs = sum(1 for k in image_keys if k)
                        self.stdout.write(
                            f"  [{sku}] {name[:45]} | Cat={cat_name} "
                            f"Marca={brand_name or '-'} | ${price} | "
                            f"{len(features)} carac, {len(specs)} espec, {imgs} img"
                        )
                        continue

                    category, _ = Category.objects.get_or_create(name=cat_name)
                    brand = None
                    if brand_name:
                        brand, _ = Brand.objects.get_or_create(name=brand_name)

                    defaults = {
                        "description": name,
                        "long_description": long_desc,
                        "category": category,
                        "brand": brand,
                        "sale_price": price,
                        "features": features,
                        "specifications": specs,
                        "image1": image_keys[0] or None,
                        "image2": image_keys[1] or None,
                        "image3": image_keys[2] or None,
                        "image4": image_keys[3] or None,
                        "is_active": True,
                    }
                    _, was_created = Product.objects.update_or_create(
                        sku=sku, defaults=defaults
                    )
                    if was_created:
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f"  [+] {sku} {name[:45]}"))
                    else:
                        updated += 1
                        self.stdout.write(f"  [~] {sku} {name[:45]} (actualizado)")
                except Exception as exc:  # noqa: BLE001
                    errores.append((i, row[COL_SKU] if len(row) > 1 else "?", str(exc)))
                    self.stdout.write(
                        self.style.ERROR(f"  [ERROR fila {i}] {exc}")
                    )

            if errores and not dry_run:
                # Si hubo errores, aborta TODO (transaccion) para no dejar carga parcial.
                raise CommandError(
                    f"{len(errores)} fila(s) con error; no se guardo nada. "
                    "Corrige el CSV y reintenta."
                )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n(DRY-RUN) Sin cambios en la base."))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nListo: {created} creados, {updated} actualizados."
                )
            )


class _NullCtx:
    """Context manager no-op para el modo dry-run."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
