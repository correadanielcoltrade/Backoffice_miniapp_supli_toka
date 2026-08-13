from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TermsView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls + [
    path("terms/", TermsView.as_view(), name="terms"),
]
