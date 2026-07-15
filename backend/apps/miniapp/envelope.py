"""
Envelope de respuesta unificado que exige Wigilabs para el BFF /v1.

Exito:  { "data": {...}, "pagination": {...}? }
Error:  { "error": { "code": "...", "message": "...", "details": [...] } }

Regla clave: la semantica HTTP es real (2xx exito, 4xx error de cliente,
5xx error del proveedor). NUNCA se responde HTTP 200 con un error embebido.
"""
from rest_framework import status as http_status
from rest_framework.response import Response


def data_response(data, pagination=None, status=http_status.HTTP_200_OK):
    """Respuesta de exito con el envelope { data, pagination? }."""
    body = {"data": data}
    if pagination is not None:
        body["pagination"] = pagination
    return Response(body, status=status)


def error_response(code, message, details=None,
                   status=http_status.HTTP_400_BAD_REQUEST):
    """Respuesta de error con el envelope { error: { code, message, details } }."""
    return Response(
        {"error": {"code": code, "message": message, "details": details or []}},
        status=status,
    )


def build_pagination(page, page_size, total):
    """Bloque de paginacion estandar para las listas."""
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    }
