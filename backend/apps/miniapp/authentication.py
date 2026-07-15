"""
Autenticacion del BFF por sessionToken.

El sessionToken es un JWT PROPIO de Supli (HS256 firmado con SECRET_KEY), no el
accessToken de Toka. Lleva el id del Customer y el userId de Toka. Su duracion
es configurable por .env (SESSION_TOKEN_LIFETIME_MIN, default 60 min).
"""
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from apps.orders.models import Customer

SESSION_TOKEN_TYPE = "miniapp_session"


def _ttl_minutes() -> int:
    return int(getattr(settings, "MINIAPP_SESSION_TTL_MIN", 60))


def issue_session_token(customer) -> tuple[str, int]:
    """
    Emite un sessionToken para el Customer dado.
    Devuelve (token, expiresIn_segundos).
    """
    now = datetime.now(timezone.utc)
    ttl_min = _ttl_minutes()
    exp = now + timedelta(minutes=ttl_min)
    payload = {
        "sub": str(customer.id),
        "tuid": customer.toka_customer_id,
        "typ": SESSION_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    # PyJWT>=2 devuelve str; por compatibilidad, normaliza a str.
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token, ttl_min * 60


class SessionTokenAuthentication(authentication.BaseAuthentication):
    """Valida el header 'Authorization: Bearer <sessionToken>'."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword.lower().encode():
            return None  # deja que otros authenticators / permisos decidan
        if len(header) == 1:
            raise exceptions.AuthenticationFailed(
                "Falta el sessionToken en el header Authorization."
            )
        if len(header) > 2:
            raise exceptions.AuthenticationFailed(
                "El header Authorization esta mal formado."
            )

        token = header[1].decode("utf-8")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("El sessionToken expiro.")
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed("sessionToken invalido.")

        if payload.get("typ") != SESSION_TOKEN_TYPE:
            raise exceptions.AuthenticationFailed("Tipo de token no valido.")

        try:
            customer = Customer.objects.get(pk=payload.get("sub"))
        except (Customer.DoesNotExist, ValueError, TypeError):
            raise exceptions.AuthenticationFailed("El cliente ya no existe.")

        return (customer, token)

    def authenticate_header(self, request):
        # Provoca 401 (en vez de 403) cuando falta el token.
        return self.keyword
