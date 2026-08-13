from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """Roles del back office."""

    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    PROCUREMENT = "PROCUREMENT", "Procurement"
    LOGISTIC = "LOGISTIC", "Logistic"
    SALES = "SALES", "Sales"


class User(AbstractUser):
    """
    Usuario del back office con rol.
    Se usa email como identificador principal ademas del username.
    """

    email = models.EmailField("correo electronico", unique=True)
    role = models.CharField(
        "rol",
        max_length=20,
        choices=Role.choices,
        default=Role.SALES,
    )
    phone = models.CharField("telefono", max_length=30, blank=True)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_administrador(self):
        return self.role == Role.ADMINISTRADOR


class TermsAndConditions(models.Model):
    """
    Terminos y condiciones de compra. Es un singleton: siempre existe un unico
    registro (pk=1) que se edita desde el back office y se sirve a la mini app.
    """

    content = models.TextField("contenido", blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Usuario que edito los terminos por ultima vez.",
    )

    class Meta:
        verbose_name = "terminos y condiciones"
        verbose_name_plural = "terminos y condiciones"

    def __str__(self):
        return "Terminos y condiciones de compra"

    @classmethod
    def load(cls):
        """Devuelve el unico registro, creandolo vacio si aun no existe."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
