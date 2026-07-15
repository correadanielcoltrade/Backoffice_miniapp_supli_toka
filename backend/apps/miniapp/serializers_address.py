"""Serializer de direcciones del BFF (formato MX de Wigilabs, camelCase)."""
import re

from rest_framework import serializers
from rest_framework.exceptions import APIException

from apps.orders.models import CustomerAddress

# CP mexicano: exactamente 5 digitos numericos.
_ZIP_RE = re.compile(r"^\d{5}$")


class InvalidZipCodeError(APIException):
    """CP con formato invalido -> HTTP 422 (distinto del 400 de campo faltante)."""

    status_code = 422
    default_code = "INVALID_ZIP_CODE"
    default_detail = "El codigo postal debe tener 5 digitos numericos (formato MX)."


class AddressSerializer(serializers.ModelSerializer):
    addressId = serializers.IntegerField(source="id", read_only=True)
    customLabel = serializers.CharField(
        source="custom_label", required=False, allow_blank=True
    )
    completeAddress = serializers.CharField(source="complete_address")
    noStreetNumber = serializers.BooleanField(
        source="no_street_number", required=False
    )
    locality = serializers.CharField(required=False, allow_blank=True)
    zipCode = serializers.CharField(
        source="zip_code", required=False, allow_blank=True
    )
    unknownZipCode = serializers.BooleanField(
        source="unknown_zip_code", required=False
    )
    supplementaryAddress = serializers.CharField(
        source="supplementary_address", required=False, allow_blank=True
    )
    deliveryInstructions = serializers.CharField(
        source="delivery_instructions", required=False, allow_blank=True
    )
    isDefault = serializers.BooleanField(source="is_default", required=False)

    class Meta:
        model = CustomerAddress
        fields = [
            "addressId",
            "label",
            "customLabel",
            "completeAddress",
            "noStreetNumber",
            "state",
            "municipality",
            "locality",
            "suburb",
            "zipCode",
            "unknownZipCode",
            "supplementaryAddress",
            "deliveryInstructions",
            "isDefault",
        ]
        extra_kwargs = {
            "state": {"required": True},
            "municipality": {"required": True},
            "suburb": {"required": True},
        }

    def validate(self, attrs):
        # label="OTHER" exige customLabel (spec Endpoint 11 -> HTTP 400).
        label = attrs.get("label", getattr(self.instance, "label", None))
        custom_label = attrs.get(
            "custom_label", getattr(self.instance, "custom_label", "")
        )
        if label == CustomerAddress.Label.OTHER and not custom_label:
            raise serializers.ValidationError(
                {"customLabel": "Requerido cuando label es 'OTHER'."}
            )

        # El CP es obligatorio salvo que el usuario indique que no lo conoce.
        unknown = attrs.get(
            "unknown_zip_code",
            getattr(self.instance, "unknown_zip_code", False),
        )
        zip_code = attrs.get(
            "zip_code", getattr(self.instance, "zip_code", "")
        )
        if not unknown:
            if not zip_code:
                raise serializers.ValidationError(
                    {"zipCode": "Requerido salvo que 'unknownZipCode' sea verdadero."}
                )
            # CP presente pero mal formado -> 422 (no 400).
            if not _ZIP_RE.match(zip_code):
                raise InvalidZipCodeError()
        return attrs
