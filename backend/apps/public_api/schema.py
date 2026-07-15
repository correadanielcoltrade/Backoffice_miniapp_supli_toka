"""
Extension para que drf-spectacular documente la autenticacion por API Key
(header X-API-Key) en la API publica.
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyAuthScheme(OpenApiAuthenticationExtension):
    target_class = "apps.public_api.authentication.ApiKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key del consumidor externo. Ej: 'tok_xxxxx'.",
        }
