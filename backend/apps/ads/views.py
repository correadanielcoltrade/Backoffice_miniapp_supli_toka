from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from apps.users.models import Role
from apps.users.permissions import HasRole

from .models import Carousel, CarouselImage
from .serializers import CarouselImageSerializer, CarouselSerializer


class CarouselViewSet(viewsets.ModelViewSet):
    queryset = Carousel.objects.prefetch_related("images").all()
    serializer_class = CarouselSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES]
    filterset_fields = ["is_active"]
    search_fields = ["name"]


class CarouselImageViewSet(viewsets.ModelViewSet):
    queryset = CarouselImage.objects.select_related("carousel").all()
    serializer_class = CarouselImageSerializer
    permission_classes = [HasRole]
    allowed_roles = [Role.SALES]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["carousel"]
