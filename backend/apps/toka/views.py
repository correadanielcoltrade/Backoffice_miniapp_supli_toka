"""
Endpoints de integracion con la Super App de Toka (User Information).

Flujo real (segun la SOP de Toka):
  1. El FRONTEND del mini-program obtiene un authCode con un JSAPI
     (my.getUserContactInformationAuthCode / ...AddressInformation... etc.).
  2. Ese authCode se envia a estos endpoints del back office.
  3. El back office llama Apply Token -> obtiene accessToken + userId.
  4. Con el accessToken llama Query User Info -> datos del usuario.
  5. Se mapean a los 8 campos de entrega del pedido y se persiste el cliente.

Nota: la info que devuelve Toka depende de los SCOPES autorizados al generar
el authCode. La direccion llega como una sola cadena (`address`); los subcampos
estructurados (colonia, CP, etc.) quedan para que el operador los complete.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Customer

from .client import TokaAPIError, TokaClient


def _toka_error_response(resp):
    """Traduce una respuesta de negocio fallida de Toka a un 502 legible."""
    return Response(
        {
            "detail": "Toka respondio con un error de negocio.",
            "resultStatus": resp.result_status,
            "resultCode": resp.result_code,
            "resultMessage": resp.result_message,
            "signature_ok": resp.signature_ok,
        },
        status=status.HTTP_502_BAD_GATEWAY,
    )


def map_user_info_to_prefill(data: dict) -> dict:
    """
    Mapea la respuesta de Query User Info a los 8 campos de entrega del pedido.
    Toka entrega la direccion como una sola cadena -> full_address. Los subcampos
    estructurados quedan vacios para que el operador los complete/edite.
    """
    full_name = data.get("fullName") or " ".join(
        p for p in [
            data.get("firstName", ""),
            data.get("secondName", ""),
            data.get("lastName", ""),
        ] if p
    ).strip()
    return {
        "recipient_name": full_name,
        "contact_number": data.get("mobilePhone", ""),
        "full_address": data.get("address", ""),
        "address_complement": "",
        "colonia": "",
        "city_alcaldia": "",
        "state": "",
        "postal_code": "",
        # extra util (no son parte de los 8, pero sirven para el cliente)
        "email": data.get("email", ""),
    }


class TokaApplyTokenView(APIView):
    """
    Intercambia un authCode por un accessToken (aislado, util para pruebas).

    POST /api/toka/apply-token/
    body: { "authCode": "..." }   o   { "refreshToken": "..." }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT,
                   description="Apply Token: authCode -> accessToken.")
    def post(self, request):
        auth_code = request.data.get("authCode")
        refresh_token = request.data.get("refreshToken")
        client = TokaClient()
        try:
            if refresh_token:
                resp = client.apply_token(
                    refresh_token=refresh_token, grant_type="REFRESH_TOKEN"
                )
            else:
                resp = client.apply_token(auth_code=auth_code)
        except TokaAPIError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        if resp.result_status != "S":
            return _toka_error_response(resp)

        return Response(
            {
                "userId": resp.data.get("userId"),
                "accessToken": resp.data.get("accessToken"),
                "accessTokenExpiryTime": resp.data.get("accessTokenExpiryTime"),
                "refreshToken": resp.data.get("refreshToken"),
                "refreshTokenExpiryTime": resp.data.get("refreshTokenExpiryTime"),
                "signature_ok": resp.signature_ok,
            },
            status=status.HTTP_200_OK,
        )


class TokaResolveUserView(APIView):
    """
    Flujo completo: authCode -> Apply Token -> Query User Info -> 8 campos de
    entrega + persistencia del cliente. Es el que consume el modulo de Pedidos.

    POST /api/toka/order-prefill/
    body: { "authCode": "..." }
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT,
                   description="authCode -> datos del usuario -> 8 campos del pedido.")
    def post(self, request):
        auth_code = request.data.get("authCode")
        if not auth_code:
            return Response(
                {"detail": "Falta 'authCode' (lo genera el JSAPI del mini-program)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client = TokaClient()
        try:
            token_resp = client.apply_token(auth_code=auth_code)
            if token_resp.result_status != "S":
                return _toka_error_response(token_resp)

            access_token = token_resp.data.get("accessToken")
            user_id = token_resp.data.get("userId")

            info_resp = client.query_user_info(access_token)
            if info_resp.result_status != "S":
                return _toka_error_response(info_resp)
        except TokaAPIError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        prefill = map_user_info_to_prefill(info_resp.data)

        # Persiste/actualiza el cliente identificado por su userId de Toka.
        customer, _ = Customer.objects.update_or_create(
            toka_customer_id=str(user_id),
            defaults={
                "full_name": prefill["recipient_name"],
                "contact_number": prefill["contact_number"],
                "email": prefill["email"],
            },
        )

        return Response(
            {
                "customer_id": customer.id,
                "toka_user_id": user_id,
                "signature_ok": token_resp.signature_ok and info_resp.signature_ok,
                **prefill,
            },
            status=status.HTTP_200_OK,
        )
