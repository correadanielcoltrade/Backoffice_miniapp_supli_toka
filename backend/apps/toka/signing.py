"""
Firma y verificacion de mensajes para la OpenAPI de Toka (esquema Antom/AMS).

Basado en el documento "Solucion de validacion de firmas" de Toka:

  - Algoritmo:  SHA256withRSA
  - keyVersion: 1
  - Codificacion de la firma: Base64 estandar y luego URL-encode (percent-encoding)

  Contenido a firmar en una SOLICITUD (6 partes, separadas por punto):
      <Metodo>.<URI>.<Client-Id>.<Request-Id>.<Request-Time>.<Body>

  Contenido a verificar en una RESPUESTA (3 partes):
      <Client-Id>.<Response-Time>.<Body>

IMPORTANTE: el <Body> que se firma debe ser EXACTAMENTE el mismo texto (mismos
bytes) que viaja en el cuerpo HTTP. Por eso serializamos el JSON una sola vez y
usamos esa misma cadena para firmar y para enviar.
"""
from __future__ import annotations

import base64
from urllib.parse import quote, unquote

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def _load_private_key(pem_text: str):
    return serialization.load_pem_private_key(pem_text.encode("utf-8"), password=None)


def _load_public_key(pem_text: str):
    return serialization.load_pem_public_key(pem_text.encode("utf-8"))


def build_request_content(method: str, uri: str, client_id: str,
                          request_id: str, request_time: str, body: str) -> str:
    """Arma el Content_To_Be_Signed de una solicitud (6 partes)."""
    return f"{method}.{uri}.{client_id}.{request_id}.{request_time}.{body}"


def build_response_content(client_id: str, response_time: str, body: str) -> str:
    """Arma el Content_To_Be_Validated de una respuesta (3 partes)."""
    return f"{client_id}.{response_time}.{body}"


def sign(content: str, private_key_pem: str) -> str:
    """
    Firma `content` con la llave privada (nuestra) y devuelve la firma lista para
    el header: Base64 estandar + URL-encode, tal como en el codigo Java de Toka.
    """
    private_key = _load_private_key(private_key_pem)
    signature = private_key.sign(
        content.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    b64 = base64.b64encode(signature).decode("ascii")
    # Java usa URLEncoder.encode(...) -> percent-encoding (space como +).
    return quote(b64, safe="")


def verify(content: str, signature_value: str, public_key_pem: str) -> bool:
    """
    Verifica la firma de una respuesta usando la llave publica de Toka.
    `signature_value` es el valor tal cual viene en el header (URL-encoded).
    """
    if not signature_value:
        return False
    public_key = _load_public_key(public_key_pem)
    raw = base64.b64decode(unquote(signature_value))
    try:
        public_key.verify(
            raw,
            content.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except InvalidSignature:
        return False


def build_signature_header(signature_value: str, key_version: int = 1) -> str:
    """Ensambla el header Signature completo."""
    return (
        f"algorithm=SHA256withRSA,keyVersion={key_version},"
        f"signature={signature_value}"
    )


def parse_signature_header(header_value: str) -> dict:
    """
    Convierte 'algorithm=SHA256withRSA,keyVersion=1,signature=xxx' en un dict.
    El valor de signature puede contener '=' (padding base64), asi que solo
    partimos en el primer '='.
    """
    out: dict[str, str] = {}
    if not header_value:
        return out
    for part in header_value.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out
