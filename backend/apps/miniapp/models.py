"""
Modelos del BFF de la mini-app.

MiniAppSession guarda, por cliente, los tokens de Toka (accessToken/refreshToken
y sus expiraciones absolutas). El accessToken/refreshToken de Toka NUNCA se
expone al front del mini-program: vive aqui, del lado del servidor, y se usa
para renovar de forma silenciosa. Supli emite su propio sessionToken (JWT
firmado con SECRET_KEY) que es lo unico que viaja al front.
"""
from django.db import models


class MiniAppSession(models.Model):
    """Estado de sesion Toka por cliente (tokens del proveedor, server-side)."""

    customer = models.OneToOneField(
        "orders.Customer",
        on_delete=models.CASCADE,
        related_name="miniapp_session",
        verbose_name="cliente",
    )
    toka_user_id = models.CharField("userId Toka", max_length=64, db_index=True)

    toka_access_token = models.TextField("accessToken Toka", blank=True)
    toka_access_expiry = models.DateTimeField(
        "expira accessToken", null=True, blank=True
    )
    toka_refresh_token = models.TextField("refreshToken Toka", blank=True)
    toka_refresh_expiry = models.DateTimeField(
        "expira refreshToken", null=True, blank=True
    )
    # Scopes acumulados que el usuario ha autorizado (lista JSON).
    granted_scopes = models.JSONField("scopes autorizados", default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "sesion mini-app"
        verbose_name_plural = "sesiones mini-app"

    def __str__(self):
        return f"Sesion {self.toka_user_id} ({self.customer_id})"
