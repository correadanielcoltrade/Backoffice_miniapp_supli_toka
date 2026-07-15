"""
Endpoints 11-13 de Wigilabs: libreta de direcciones del usuario (formato MX).

  GET   /v1/users/me/addresses            -> lista (max 3)
  POST  /v1/users/me/addresses            -> crear (201, max 3)
  PATCH /v1/users/me/addresses/{id}       -> editar parcial

Todos requieren Bearer sessionToken; operan solo sobre las direcciones del
cliente autenticado.
"""
from rest_framework import status as http_status
from rest_framework.exceptions import NotFound

from apps.orders.models import CustomerAddress

from .base import MiniAppAuthView
from .envelope import data_response, error_response
from .serializers_address import AddressSerializer


def _sync_default(customer, address):
    """Si la direccion quedo como predeterminada, desmarca las demas."""
    if address.is_default:
        customer.addresses.exclude(pk=address.pk).filter(is_default=True).update(
            is_default=False
        )


def _get_owned(customer, address_id):
    try:
        return customer.addresses.get(pk=address_id)
    except CustomerAddress.DoesNotExist:
        raise NotFound("Direccion no encontrada.")


class AddressListCreateView(MiniAppAuthView):
    def get(self, request):
        qs = request.user.addresses.all()
        return data_response(AddressSerializer(qs, many=True).data)

    def post(self, request):
        customer = request.user
        if customer.addresses.count() >= CustomerAddress.MAX_PER_CUSTOMER:
            return error_response(
                "ADDRESS_LIMIT_REACHED",
                f"Solo se permiten {CustomerAddress.MAX_PER_CUSTOMER} direcciones por usuario.",
                status=http_status.HTTP_409_CONFLICT,
            )
        ser = AddressSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        address = ser.save(customer=customer)
        _sync_default(customer, address)
        return data_response(
            AddressSerializer(address).data, status=http_status.HTTP_201_CREATED
        )


class AddressDetailView(MiniAppAuthView):
    def patch(self, request, address_id):
        customer = request.user
        address = _get_owned(customer, address_id)
        ser = AddressSerializer(address, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        address = ser.save()
        _sync_default(customer, address)
        return data_response(AddressSerializer(address).data)
