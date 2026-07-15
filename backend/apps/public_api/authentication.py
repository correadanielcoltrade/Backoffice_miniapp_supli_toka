"""Autenticacion por API Key para consumidores externos."""
from django.utils import timezone
from rest_framework import authentication, exceptions

from .models import ApiClient, hash_key

API_KEY_HEADER = "X-API-Key"


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """
    Lee la API Key del header 'X-API-Key', valida contra los consumidores
    activos y deja el ApiClient en request.user / request.auth.
    """

    def authenticate(self, request):
        raw_key = request.headers.get(API_KEY_HEADER)
        if not raw_key:
            return None  # Sin credencial -> IsAuthenticated devolvera 401

        try:
            client = ApiClient.objects.get(
                hashed_key=hash_key(raw_key), is_active=True
            )
        except ApiClient.DoesNotExist:
            raise exceptions.AuthenticationFailed("API Key invalida o inactiva.")

        # Marca de uso (sin bloquear la request si falla)
        ApiClient.objects.filter(pk=client.pk).update(last_used_at=timezone.now())

        return (client, client)

    def authenticate_header(self, request):
        # Provoca respuesta 401 (en vez de 403) cuando falta la credencial
        return API_KEY_HEADER
