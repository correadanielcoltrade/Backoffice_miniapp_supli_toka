"""Endpoints de contenido de Wigilabs: banners (Ads) y terminos y condiciones."""
from datetime import timezone as _tz

from django.db.models import Q
from django.utils import timezone

from apps.ads.models import CarouselImage
from apps.users.models import TermsAndConditions

from .base import MiniAppFlexibleAuthView
from .envelope import data_response
from .serializers import BannerSerializer


class BannersView(MiniAppFlexibleAuthView):
    """
    GET /v1/content/banners -> banners de carruseles VIGENTES.
    Un carrusel es vigente si esta activo (interruptor) Y estamos dentro de su
    ventana de programacion: active_from <= ahora <= active_until (cualquiera de
    las dos fechas puede estar vacia = sin limite por ese lado).
    """

    def get(self, request):
        now = timezone.now()
        qs = (
            CarouselImage.objects
            .filter(carousel__is_active=True)
            .filter(
                Q(carousel__active_from__isnull=True)
                | Q(carousel__active_from__lte=now)
            )
            .filter(
                Q(carousel__active_until__isnull=True)
                | Q(carousel__active_until__gte=now)
            )
            .order_by("position", "created_at")
        )
        data = BannerSerializer(qs, many=True, context={"request": request}).data
        return data_response(data)


class TermsView(MiniAppFlexibleAuthView):
    """
    GET /v1/content/terms -> terminos y condiciones de compra (texto).
    Se muestran al cliente en la mini app (p. ej. antes de confirmar la compra).
    """

    def get(self, request):
        terms = TermsAndConditions.load()
        updated = terms.updated_at
        return data_response({
            "content": terms.content or "",
            "updatedAt": (
                updated.astimezone(_tz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                if updated else None
            ),
        })
