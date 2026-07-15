"""
Cliente HTTP firmado para la OpenAPI de Toka (UAT/Prod).

Cada solicitud se firma con NUESTRA llave privada (SHA256withRSA) y cada
respuesta se verifica con la llave publica de Toka. Ver apps/toka/signing.py
para el detalle del esquema.
"""
import json
import time
import uuid
from pathlib import Path

import requests
from django.conf import settings

from . import signing


class TokaAPIError(Exception):
    pass


def _read_key(path: str, label: str) -> str:
    if not path:
        raise TokaAPIError(f"Falta configurar la ruta de la llave: {label}.")
    p = Path(path)
    if not p.exists():
        raise TokaAPIError(f"No se encontro el archivo de llave ({label}): {path}")
    return p.read_text(encoding="utf-8")


class TokaResponse:
    """Envuelve la respuesta de Toka con el resultado de la verificacion de firma."""

    def __init__(self, status_code, body_text, headers, signature_ok, data):
        self.status_code = status_code
        self.body_text = body_text
        self.headers = headers
        self.signature_ok = signature_ok
        self.data = data or {}

    @property
    def result(self) -> dict:
        return self.data.get("result", {}) if isinstance(self.data, dict) else {}

    @property
    def result_code(self) -> str:
        return self.result.get("resultCode", "")

    @property
    def result_status(self) -> str:
        return self.result.get("resultStatus", "")

    @property
    def result_message(self) -> str:
        return self.result.get("resultMessage", "")


class TokaClient:
    def __init__(self, base_url=None, client_id=None, timeout=20):
        self.base_url = (base_url or settings.TOKA_API_BASE_URL).rstrip("/")
        self.client_id = client_id or settings.TOKA_CLIENT_ID
        self.timeout = timeout

    def post(self, uri: str, payload: dict) -> TokaResponse:
        """
        Envia una solicitud POST firmada a `uri` (ej. '/v1/acquiring/recon/get').
        Devuelve un TokaResponse con la firma de respuesta ya verificada.
        """
        if not self.base_url:
            raise TokaAPIError("Falta TOKA_API_BASE_URL en el .env.")
        if not self.client_id:
            raise TokaAPIError("Falta TOKA_CLIENT_ID en el .env.")

        private_key = _read_key(settings.TOKA_PRIVATE_KEY_PATH, "privada Supli")
        toka_public_key = _read_key(
            settings.TOKA_TOKA_PUBLIC_KEY_PATH, "publica de Toka"
        )

        # El body debe firmarse EXACTAMENTE como se envia -> serializar una sola vez.
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        request_id = uuid.uuid4().hex
        request_time = str(int(time.time() * 1000))  # milisegundos

        content = signing.build_request_content(
            "POST", uri, self.client_id, request_id, request_time, body
        )
        signature_value = signing.sign(content, private_key)

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Client-Id": self.client_id,
            "Request-Id": request_id,
            "Request-Time": request_time,
            "Signature": signing.build_signature_header(signature_value, 1),
        }

        # Verificacion TLS: usa el CA bundle si esta configurado; si no, el booleano.
        verify = settings.TOKA_CA_BUNDLE or settings.TOKA_VERIFY_SSL
        if verify is False:
            # Evita el ruido de InsecureRequestWarning cuando se desactiva en UAT.
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        url = f"{self.base_url}{uri}"
        try:
            resp = requests.post(
                url,
                data=body.encode("utf-8"),
                headers=headers,
                timeout=self.timeout,
                verify=verify,
            )
        except requests.RequestException as exc:
            raise TokaAPIError(f"Error de red al llamar a Toka: {exc}") from exc

        # Verificar la firma de la respuesta (Client-Id.Response-Time.Body)
        resp_client_id = resp.headers.get("Client-Id", self.client_id)
        resp_time = resp.headers.get("Response-Time", "")
        sig_header = signing.parse_signature_header(resp.headers.get("Signature", ""))
        resp_signature = sig_header.get("signature", "")

        signature_ok = False
        if resp_time and resp_signature:
            resp_content = signing.build_response_content(
                resp_client_id, resp_time, resp.text
            )
            signature_ok = signing.verify(
                resp_content, resp_signature, toka_public_key
            )

        try:
            data = resp.json()
        except ValueError:
            data = None

        return TokaResponse(
            status_code=resp.status_code,
            body_text=resp.text,
            headers=dict(resp.headers),
            signature_ok=signature_ok,
            data=data,
        )

    # ------------------------------------------------------------------
    # Flujos de usuario (User Information)
    # ------------------------------------------------------------------
    def _require_app_id(self) -> str:
        app_id = settings.TOKA_APP_ID
        if not app_id:
            raise TokaAPIError(
                "Falta TOKA_APP_ID en el .env (el appId del mini-program que "
                "entrega Toka). Sin el, Apply Token / Query User Info no funcionan."
            )
        return app_id

    def apply_token(self, auth_code=None, refresh_token=None,
                    grant_type="AUTHORIZATION_CODE") -> TokaResponse:
        """
        POST /v2/authorizations/applyToken
        Intercambia un authCode (obtenido por el JSAPI del mini-program) por un
        accessToken. Con grant_type=REFRESH_TOKEN usa refresh_token en su lugar.
        """
        payload = {"appId": self._require_app_id(), "grantType": grant_type}
        if grant_type == "AUTHORIZATION_CODE":
            if not auth_code:
                raise TokaAPIError("Se requiere auth_code para AUTHORIZATION_CODE.")
            payload["authCode"] = auth_code
        elif grant_type == "REFRESH_TOKEN":
            if not refresh_token:
                raise TokaAPIError("Se requiere refresh_token para REFRESH_TOKEN.")
            payload["refreshToken"] = refresh_token
        return self.post("/v2/authorizations/applyToken", payload)

    def query_user_info(self, access_token: str) -> TokaResponse:
        """
        POST /v2/users/inquiryUserInfo
        Devuelve la informacion del usuario segun los scopes que se autorizaron
        al generar el authCode (nombre, telefono, direccion, etc.).
        """
        if not access_token:
            raise TokaAPIError("Se requiere access_token para consultar el usuario.")
        payload = {"appId": self._require_app_id(), "accessToken": access_token}
        return self.post("/v2/users/inquiryUserInfo", payload)

    # ------------------------------------------------------------------
    # Flujos de pago (Mini-Program Payment)  ·  Fase 4
    # ------------------------------------------------------------------
    # Contrato oficial: Mini-Program Collaboration SOP v1.7 (ver la skill
    # tokapay-integration-guide, references/miniapp-integration.md).
    #
    #   Crear pago : POST /v2/acquiring/miniprogram/create  (productCode
    #                MINI_PROGRAM_DIRECT_PAY) -> paymentId + paymentUrl
    #   Consultar  : POST /v1/acquiring/payment/inquiry  (por paymentId, v1)
    #
    # OJO: create devuelve resultStatus "A" (20000006 Accept Request) en el
    # camino feliz, NO "S". Tratar "A" como exito.
    PAYMENT_PRODUCT_CODE = "MINI_PROGRAM_DIRECT_PAY"
    # Minutos de validez de la orden de pago (order.expiryTime, obligatorio).
    PAYMENT_EXPIRY_MINUTES = 15

    @staticmethod
    def _amount_minor(value) -> int:
        """
        Toka expresa los montos en centavos. En Mini-Program Create el campo
        order.orderAmount.value es Long (numero), no string: 10.00 MXN -> 1000.
        """
        from decimal import ROUND_HALF_UP, Decimal

        cents = (Decimal(str(value)) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return int(cents)

    def create_payment(self, *, user_id: str, merchant_trans_id: str, amount,
                       order_title: str, expiry_time: str = "",
                       goods_detail=None, currency: str = "MXN") -> TokaResponse:
        """
        POST /v2/acquiring/miniprogram/create

        user_id          userId de Toka (viene de Apply Token). Obligatorio.
        merchant_trans_id  id unico de la transaccion de NUESTRO lado (<=64).
        amount           monto en MXN (se convierte a centavos).
        order_title      texto que ve el usuario en la caja (<=256).
        expiry_time      'YYYY-MM-DD hh:mm:ss'; si se omite, ahora + 15 min.

        Devuelve paymentId (guardarlo: es la llave para consultar/reembolsar) y
        paymentUrl (el front lo pasa a my.pay).
        """
        if not user_id:
            raise TokaAPIError("Se requiere el userId de Toka para crear el pago.")
        if not merchant_trans_id:
            raise TokaAPIError("Se requiere merchant_trans_id para crear el pago.")

        if not expiry_time:
            expiry_time = self.default_expiry_time()

        order = {
            "orderTitle": order_title[:256],
            "merchantTransId": merchant_trans_id[:64],
            "orderAmount": {
                "value": self._amount_minor(amount),  # Long, en centavos
                "currency": currency,
            },
            "expiryTime": expiry_time,
        }
        if goods_detail:
            order["goodsDetail"] = goods_detail

        payload = {
            "productCode": self.PAYMENT_PRODUCT_CODE,
            "appId": self._require_app_id(),
            "userId": str(user_id),
            "order": order,
        }
        return self.post("/v2/acquiring/miniprogram/create", payload)

    def query_payment(self, *, payment_id: str) -> TokaResponse:
        """
        POST /v1/acquiring/payment/inquiry  (mismo endpoint que POS, v1)

        Consulta el estado REAL del pago por el paymentId que devolvio el create.
        Es la fuente de verdad: nunca confiar en el resultCode de my.pay (6004 =
        desconocido). La respuesta trae paymentStatus PROCESSING/SUCCESS/FAILED.
        """
        if not payment_id:
            raise TokaAPIError("Se requiere paymentId para consultar el pago.")
        return self.post("/v1/acquiring/payment/inquiry", {"paymentId": payment_id})

    @classmethod
    def default_expiry_time(cls) -> str:
        """order.expiryTime en el formato que exige Toka: 'YYYY-MM-DD hh:mm:ss'."""
        from datetime import datetime, timedelta, timezone

        expires = datetime.now(timezone.utc) + timedelta(
            minutes=cls.PAYMENT_EXPIRY_MINUTES
        )
        return expires.strftime("%Y-%m-%d %H:%M:%S")
