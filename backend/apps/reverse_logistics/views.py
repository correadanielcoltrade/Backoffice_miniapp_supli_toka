from rest_framework import viewsets

from apps.users.models import Role
from apps.users.permissions import HasRole

from .models import ReturnRequest
from .serializers import ReturnRequestSerializer


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """Modulo de Logistica Inversa (estructura base, campos por confirmar)."""

    queryset = ReturnRequest.objects.select_related("order").all()
    serializer_class = ReturnRequestSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.LOGISTIC]
    filterset_fields = ["status", "order"]
