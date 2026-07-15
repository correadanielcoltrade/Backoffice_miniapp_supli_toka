"""Permisos reutilizables basados en el rol del usuario."""
from rest_framework.permissions import BasePermission

from .models import Role


class IsAdministrador(BasePermission):
    """Solo usuarios con rol Administrador."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMINISTRADOR
        )


class HasRole(BasePermission):
    """
    Permite el acceso si el usuario tiene alguno de los roles indicados
    en el atributo `allowed_roles` de la vista. Administrador siempre pasa.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.role == Role.ADMINISTRADOR:
            return True
        allowed = getattr(view, "allowed_roles", None)
        if not allowed:
            return True
        return user.role in allowed
