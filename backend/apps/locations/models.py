from django.db import models


class MexicoPostalCode(models.Model):
    """
    Catalogo postal de Mexico (SEPOMEX). Una fila por asentamiento (colonia):
    un mismo codigo postal suele tener varias colonias.
    Se carga con el comando `import_sepomex` a partir del archivo oficial.
    """

    zip_code = models.CharField("codigo postal", max_length=5, db_index=True)
    state = models.CharField("estado", max_length=120)
    municipality = models.CharField("municipio / alcaldia", max_length=150)
    city = models.CharField("ciudad / localidad", max_length=150, blank=True)
    suburb = models.CharField("colonia / asentamiento", max_length=200)
    settlement_type = models.CharField("tipo de asentamiento", max_length=80, blank=True)

    class Meta:
        verbose_name = "codigo postal MX"
        verbose_name_plural = "codigos postales MX"
        indexes = [
            models.Index(fields=["state", "municipality"]),
            models.Index(fields=["zip_code", "suburb"]),
        ]
        ordering = ["zip_code", "suburb"]

    def __str__(self):
        return f"{self.zip_code} - {self.suburb} ({self.municipality}, {self.state})"
