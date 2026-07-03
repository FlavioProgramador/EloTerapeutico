"""Rotas públicas do módulo financeiro."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .transaction_viewset import TransactionViewSet

router = DefaultRouter()
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
]
