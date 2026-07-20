"""Rotas canônicas da API financeira v1."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.finances.api.v1.views import FinancialTransactionViewSet

router = DefaultRouter()
router.register(r"", FinancialTransactionViewSet, basename="transaction")

urlpatterns = [path("", include(router.urls))]
