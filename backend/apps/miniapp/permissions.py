from rest_framework.permissions import BasePermission


class IsMiniAppAuthenticated(BasePermission):
    """Autoriza solo si el sessionToken resolvio a un Customer valido."""

    message = "Se requiere un sessionToken valido (Authorization: Bearer)."

    def has_permission(self, request, view):
        return bool(getattr(request.user, "toka_customer_id", None))
