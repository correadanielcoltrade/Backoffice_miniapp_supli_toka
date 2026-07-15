"""Endpoint 3 de Wigilabs: banners (desde el carrusel de Ads)."""
from apps.ads.models import CarouselImage

from .base import MiniAppFlexibleAuthView
from .envelope import data_response
from .serializers import BannerSerializer


class BannersView(MiniAppFlexibleAuthView):
    """GET /v1/content/banners -> lista de banners de carruseles activos."""

    def get(self, request):
        qs = (
            CarouselImage.objects
            .filter(carousel__is_active=True)
            .order_by("position", "created_at")
        )
        data = BannerSerializer(qs, many=True, context={"request": request}).data
        return data_response(data)
