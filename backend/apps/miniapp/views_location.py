"""
Endpoint 14 de Wigilabs: catalogo de ubicaciones de Mexico (SEPOMEX).

  GET /v1/locations/by-zip-code/{zip}                     -> resuelve por CP
  GET /v1/locations/states                                -> cascada: estados
  GET /v1/locations/municipalities?state=...              -> cascada: municipios
  GET /v1/locations/suburbs?state=...&municipality=...     -> cascada: colonias

La cascada cubre el caso "no conozco mi CP". Endpoints publicos (sin token).
"""
from rest_framework.exceptions import NotFound, ValidationError

from apps.locations.models import MexicoPostalCode

from .base import MiniAppFlexibleAuthView
from .envelope import data_response


class LocationByZipView(MiniAppFlexibleAuthView):
    def get(self, request, zip_code):
        rows = list(MexicoPostalCode.objects.filter(zip_code=zip_code))
        if not rows:
            raise NotFound("Codigo postal no encontrado.")
        first = rows[0]
        # Un CP puede tener varias colonias; el resto de campos son constantes.
        suburbs = sorted({r.suburb for r in rows})
        return data_response({
            "zipCode": zip_code,
            "state": first.state,
            "municipality": first.municipality,
            "locality": first.city,
            "suburbs": suburbs,
        })


class StatesView(MiniAppFlexibleAuthView):
    def get(self, request):
        states = (
            MexicoPostalCode.objects.order_by("state")
            .values_list("state", flat=True)
            .distinct()
        )
        return data_response(list(states))


class MunicipalitiesView(MiniAppFlexibleAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        if not state:
            raise ValidationError({"state": "Parametro requerido."})
        municipalities = (
            MexicoPostalCode.objects.filter(state=state)
            .order_by("municipality")
            .values_list("municipality", flat=True)
            .distinct()
        )
        return data_response(list(municipalities))


class SuburbsView(MiniAppFlexibleAuthView):
    def get(self, request):
        state = request.query_params.get("state")
        municipality = request.query_params.get("municipality")
        if not state or not municipality:
            raise ValidationError(
                {"detail": "Los parametros 'state' y 'municipality' son requeridos."}
            )
        rows = (
            MexicoPostalCode.objects.filter(state=state, municipality=municipality)
            .order_by("suburb")
            .values("suburb", "zip_code")
            .distinct()
        )
        return data_response(
            [{"suburb": r["suburb"], "zipCode": r["zip_code"]} for r in rows]
        )
