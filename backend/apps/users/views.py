from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Role
from .permissions import IsAdministrador
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    SelfProfileSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Modulo Administrador de usuarios y Roles.
    La gestion (crear/editar/borrar) esta restringida al rol Administrador.
    """

    queryset = User.objects.all()
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "username"]

    def get_permissions(self):
        if self.action in ["me", "update_profile", "change_password"]:
            return [IsAuthenticated()]
        return [IsAdministrador()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Datos del usuario autenticado."""
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["patch"], url_path="me/profile")
    def update_profile(self, request):
        """Edicion self-service del perfil propio."""
        serializer = SelfProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        """Cambio de contrasena del usuario autenticado."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contrasena actualizada correctamente."})

    @action(detail=False, methods=["get"], url_path="roles")
    def roles(self, request):
        """Catalogo de roles disponibles para la UI."""
        return Response(
            [{"value": value, "label": label} for value, label in Role.choices]
        )
