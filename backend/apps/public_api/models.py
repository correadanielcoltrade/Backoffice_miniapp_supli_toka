import hashlib
import secrets

from django.db import models

KEY_PREFIX_LEN = 12


def hash_key(raw_key: str) -> str:
    """Hash SHA-256 de la API Key (solo se guarda el hash, nunca la clave)."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Genera una API Key nueva con prefijo identificable."""
    return f"tok_{secrets.token_urlsafe(32)}"


class ApiClient(models.Model):
    """
    Consumidor externo autorizado a usar la API publica (/api/public/v1/).
    La clave se muestra UNA sola vez al emitirla; en la base solo queda su hash.
    """

    name = models.CharField("nombre del consumidor", max_length=150)
    contact_email = models.EmailField("correo de contacto", blank=True)
    key_prefix = models.CharField(
        "prefijo de la clave", max_length=KEY_PREFIX_LEN, db_index=True
    )
    hashed_key = models.CharField(
        "hash de la clave", max_length=64, unique=True, db_index=True
    )
    is_active = models.BooleanField("activo", default=True)
    # Limite de peticiones por minuto para este consumidor
    rate_limit_per_min = models.PositiveIntegerField(
        "limite por minuto", default=60
    )
    last_used_at = models.DateTimeField("ultimo uso", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "consumidor de API"
        verbose_name_plural = "consumidores de API"
        ordering = ["name"]

    def __str__(self):
        estado = "activo" if self.is_active else "inactivo"
        return f"{self.name} ({self.key_prefix}… · {estado})"

    @staticmethod
    def issue(name, contact_email=""):
        """
        Crea un consumidor y devuelve (instancia, clave_en_claro).
        La clave en claro NO se persiste; muestrala/copiala al momento.
        """
        raw = generate_api_key()
        client = ApiClient.objects.create(
            name=name,
            contact_email=contact_email,
            key_prefix=raw[:KEY_PREFIX_LEN],
            hashed_key=hash_key(raw),
        )
        return client, raw

    def rotate_key(self):
        """Genera una nueva clave e invalida la anterior. Devuelve la clave en claro."""
        raw = generate_api_key()
        self.key_prefix = raw[:KEY_PREFIX_LEN]
        self.hashed_key = hash_key(raw)
        self.save(update_fields=["key_prefix", "hashed_key"])
        return raw

    # Permite que DRF trate al consumidor como "autenticado"
    @property
    def is_authenticated(self):
        return True
