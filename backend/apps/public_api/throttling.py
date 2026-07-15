"""Throttling por consumidor externo, usando su limite configurable."""
from rest_framework.throttling import SimpleRateThrottle

from .models import ApiClient


class ApiClientRateThrottle(SimpleRateThrottle):
    """
    Limita las peticiones por minuto segun rate_limit_per_min de cada ApiClient.
    Solo aplica cuando la request viene autenticada por API Key.
    """

    scope = "public_api"

    def get_cache_key(self, request, view):
        client = request.auth
        if not isinstance(client, ApiClient):
            return None  # No aplica si no hay API Key
        return f"throttle_public_api_{client.pk}"

    def allow_request(self, request, view):
        client = getattr(request, "auth", None)
        if isinstance(client, ApiClient):
            # Define el rate dinamicamente: "<n>/min" por consumidor
            self.rate = f"{client.rate_limit_per_min}/min"
            self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)
