"""
Endpoint 1 de Wigilabs: intercambio de sesion.

POST /v1/auth/session
body: { "authCode": "...", "scopeType": "DIGITAL_IDENTITY" }

Flujo (segun la SOP de Toka):
  authCode (lo genera el JSAPI del mini-program)
    -> Apply Token (OpenAPI)      => accessToken + userId
    -> Query User Info (OpenAPI)  => datos del usuario segun los scopes
    -> upsert Customer + MiniAppSession (tokens de Toka, server-side)
    -> emite sessionToken PROPIO de Supli

El accessToken/refreshToken de Toka NUNCA se devuelven al front.
"""
from apps.orders.models import Customer
from apps.toka.client import TokaAPIError, TokaClient

from .authentication import issue_session_token
from .base import MiniAppPublicView
from .envelope import data_response, error_response
from .toka_utils import toka_error_to_response, upsert_session

# Campos de Query User Info que se exponen al front (los que vengan segun scope).
_USER_FIELDS = [
    "userId", "nickName", "fullName", "firstName", "secondName", "lastName",
    "avatar", "gender", "birthday", "nationality", "email", "mobilePhone",
    "address", "birthState", "kycState",
]


def map_user_info(data: dict) -> dict:
    """Devuelve solo los campos presentes (no nulos/ vacios)."""
    user = {}
    for key in _USER_FIELDS:
        value = data.get(key)
        if value not in (None, ""):
            user[key] = value
    return user


class AuthSessionView(MiniAppPublicView):
    """Intercambia un authCode por un sessionToken de Supli."""

    def post(self, request):
        auth_code = (request.data or {}).get("authCode")
        scope_type = (request.data or {}).get("scopeType")
        if not auth_code:
            return error_response(
                "VALIDATION_ERROR",
                "Falta 'authCode' (lo genera el JSAPI del mini-program).",
                details=[{"field": "authCode", "message": "requerido"}],
            )

        client = TokaClient()
        try:
            token_resp = client.apply_token(auth_code=auth_code)
            if token_resp.result_status != "S":
                return toka_error_to_response(token_resp)

            access_token = token_resp.data.get("accessToken")
            user_id = token_resp.data.get("userId")

            info_resp = client.query_user_info(access_token)
            if info_resp.result_status != "S":
                return toka_error_to_response(info_resp)
        except TokaAPIError as exc:
            return error_response(
                "TOKA_UNAVAILABLE", str(exc),
                status=502,
            )

        user = map_user_info(info_resp.data)

        # Upsert del cliente identificado por su userId de Toka.
        full_name = user.get("fullName") or " ".join(
            p for p in [user.get("firstName", ""), user.get("secondName", ""),
                        user.get("lastName", "")] if p
        ).strip()
        customer, _ = Customer.objects.update_or_create(
            toka_customer_id=str(user_id),
            defaults={
                "full_name": full_name or (user.get("nickName") or str(user_id)),
                "contact_number": user.get("mobilePhone", ""),
                "email": user.get("email", ""),
            },
        )

        scopes = [scope_type] if scope_type else None
        upsert_session(customer, token_resp, scopes=scopes)

        session_token, expires_in = issue_session_token(customer)
        return data_response({
            "sessionToken": session_token,
            "tokenType": "Bearer",
            "expiresIn": expires_in,
            "user": user,
        })
