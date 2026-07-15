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
