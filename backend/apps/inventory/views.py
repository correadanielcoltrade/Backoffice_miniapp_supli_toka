from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import Role
from apps.users.permissions import HasRole

from .models import Inventory, StockMovement
from .serializers import InventorySerializer, StockMovementSerializer
from .services import apply_stock_change


class InventoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Modulo de Gestion de Inventarios.
    Permite listar productos con su stock y editar las unidades en inventario.
    """

    queryset = Inventory.objects.select_related("product", "product__category").all()
    serializer_class = InventorySerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.PROCUREMENT, Role.LOGISTIC]
    filterset_fields = ["product__category"]
    search_fields = ["product__sku", "product__description"]
    ordering_fields = ["units_in_stock", "updated_at"]

    @action(detail=True, methods=["post"], url_path="adjust")
    def adjust(self, request, pk=None):
        """Ajuste manual de stock. Body: {"change": int, "reference": str}."""
        inventory = self.get_object()
        change = int(request.data.get("change", 0))
        reference = request.data.get("reference", "")
        inventory = apply_stock_change(
            product=inventory.product,
            change=change,
            reason=StockMovement.Reason.MANUAL,
            reference=reference,
        )
        return Response(InventorySerializer(inventory).data)


class StockMovementViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = StockMovement.objects.select_related("inventory__product").all()
    serializer_class = StockMovementSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.PROCUREMENT, Role.LOGISTIC]
    filterset_fields = ["reason", "inventory"]
    ordering_fields = ["created_at"]
