"""
Vistas base del BFF /v1. Traducen cualquier excepcion de DRF al envelope de
error de Wigilabs y fijan la autenticacion adecuada por tipo de endpoint.

- MiniAppPublicView : endpoints abiertos (banners, catalogo, ubicaciones).
- MiniAppAuthView   : endpoints de usuario (Bearer sessionToken).
"""
from django.conf import settings
from rest_framework import status as http_status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import APIView

from .authentication import SessionTokenAuthentication
from .envelope import error_response
from .permissions import IsMiniAppAuthenticated


def _flatten_details(detail, field=None):
    """Convierte el detalle de una ValidationError en una lista [{field, message}]."""
    items = []
    if isinstance(detail, dict):
        for key, value in detail.items():
            items.extend(_flatten_details(value, field=key))
    elif isinstance(detail, (list, tuple)):
        for value in detail:
            items.extend(_flatten_details(value, field=field))
    else:
        items.append({"field": field, "message": str(detail)})
    return items


class MiniAppExceptionMixin:
    """Serializa las excepciones de DRF al envelope { error: {...} }."""

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return error_response(
                "VALIDATION_ERROR",
                "Los datos enviados no son validos.",
                details=_flatten_details(exc.detail),
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            return error_response(
                "UNAUTHENTICATED",
                str(exc.detail) if hasattr(exc, "detail") else str(exc),
                status=http_status.HTTP_401_UNAUTHORIZED,
            )
        if isinstance(exc, PermissionDenied):
            return error_response(
                "FORBIDDEN", str(exc.detail),
                status=http_status.HTTP_403_FORBIDDEN,
            )
        if isinstance(exc, NotFound):
            return error_response(
                "NOT_FOUND", str(exc.detail),
                status=http_status.HTTP_404_NOT_FOUND,
            )
        if isinstance(exc, MethodNotAllowed):
            return error_response(
                "METHOD_NOT_ALLOWED", str(exc.detail),
                status=http_status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        if isinstance(exc, Throttled):
            return error_response(
                "RATE_LIMITED", str(exc.detail),
                status=http_status.HTTP_429_TOO_MANY_REQUESTS,
            )
        if isinstance(exc, APIException):
            return error_response(
                getattr(exc, "default_code", "ERROR").upper(),
                str(exc.detail),
                status=exc.status_code,
            )
        # Cualquier otra excepcion no controlada -> 500 con envelope.
        return error_response(
            "INTERNAL_ERROR",
            "Ocurrio un error inesperado en el servidor.",
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class MiniAppPublicView(MiniAppExceptionMixin, APIView):
    """
    Endpoints SIEMPRE abiertos del BFF (sin sessionToken). Solo aplica a
    auth/session, que es el que EMITE el token y por definicion no puede exigirlo.
    """

    authentication_classes = []
    permission_classes = []


class MiniAppFlexibleAuthView(MiniAppExceptionMixin, APIView):
    """
    Endpoints de catalogo / contenido / ubicaciones.

    Por defecto exigen 'Bearer sessionToken' (MINIAPP_PUBLIC_CATALOG=False).
    Poniendo MINIAPP_PUBLIC_CATALOG=True en el .env vuelven a ser publicos, como
    propone la spec de Wigilabs (catalogo sin PII, home visible antes del login).
    La decision se lee por peticion: cambiar el flag NO requiere tocar codigo.
    """

    def _public(self) -> bool:
        return bool(getattr(settings, "MINIAPP_PUBLIC_CATALOG", False))

    def get_authenticators(self):
        return [] if self._public() else [SessionTokenAuthentication()]

    def get_permissions(self):
        return [] if self._public() else [IsMiniAppAuthenticated()]


class MiniAppAuthView(MiniAppExceptionMixin, APIView):
    """Endpoints de usuario del BFF (requieren Bearer sessionToken)."""

    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsMiniAppAuthenticated]

    @property
    def customer(self):
        """El Customer autenticado por el sessionToken."""
        return self.request.user
