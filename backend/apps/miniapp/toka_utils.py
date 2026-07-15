"""
Utilidades puente entre el BFF y la OpenAPI de Toka: conversion de timestamps,
persistencia de la sesion (tokens de Toka) y mapeo de errores de negocio de
Toka al envelope de error de Wigilabs con el codigo HTTP correcto.
"""
from datetime import datetime, timezone

from rest_framework import status as http_status

from .envelope import error_response
from .models import MiniAppSession

# authCode caduco/usado o refreshToken inexistente = error del cliente (4xx).
# El resto (client-id, firma, appId, permisos, merchant) = error del proveedor (5xx).
_TOKA_CLIENT_ERRORS = {
    "20040001": ("TOKA_AUTHCODE_INVALID",
                 "El authCode no existe o ya fue utilizado."),
    "20040002": ("TOKA_REFRESH_INVALID",
                 "El refreshToken no existe."),
    "20040005": ("TOKA_ACCESSTOKEN_EXPIRED",
                 "El accessToken de Toka expiro."),
    "20040006": ("TOKA_ACCESSTOKEN_UNAVAILABLE",
                 "El accessToken de Toka no esta disponible."),
}


def ms_to_datetime(value):
    """Convierte un timestamp de Toka (ms, str o int) a datetime aware UTC."""
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    except (ValueError, TypeError):
        return None


def toka_error_to_response(resp):
    """
    Traduce una respuesta de negocio fallida de Toka al envelope de error.
    4xx si el problema es atribuible al cliente (authCode); 5xx si es del
    proveedor (firma, client-id, appId, permisos...).
    """
    code = resp.result_code or ""
    if code in _TOKA_CLIENT_ERRORS:
        envelope_code, message = _TOKA_CLIENT_ERRORS[code]
        return error_response(
            envelope_code,
            message,
            details=[{"tokaResultCode": code,
                      "tokaResultMessage": resp.result_message}],
            status=http_status.HTTP_400_BAD_REQUEST,
        )
    return error_response(
        "TOKA_ERROR",
        "El proveedor (Toka) rechazo la solicitud.",
        details=[{"tokaResultCode": code,
                  "tokaResultMessage": resp.result_message,
                  "signatureOk": resp.signature_ok}],
        status=http_status.HTTP_502_BAD_GATEWAY,
    )


def upsert_session(customer, token_resp, scopes=None):
    """
    Guarda/actualiza la MiniAppSession con los tokens de Toka. Acumula los
    scopes autorizados (no pisa los anteriores).
    """
    data = token_resp.data
    session, _ = MiniAppSession.objects.get_or_create(customer=customer)
    session.toka_user_id = str(data.get("userId") or session.toka_user_id or "")

    access = data.get("accessToken")
    refresh = data.get("refreshToken")
    if access:
        session.toka_access_token = access
        session.toka_access_expiry = ms_to_datetime(
            data.get("accessTokenExpiryTime")
        )
    if refresh:
        session.toka_refresh_token = refresh
        session.toka_refresh_expiry = ms_to_datetime(
            data.get("refreshTokenExpiryTime")
        )

    if scopes:
        merged = set(session.granted_scopes or []) | set(scopes)
        session.granted_scopes = sorted(merged)

    session.save()
    return session
