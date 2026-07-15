from django.urls import path

from .views import SalesSummaryView

urlpatterns = [
    path("reports/summary/", SalesSummaryView.as_view(), name="reports-summary"),
]
