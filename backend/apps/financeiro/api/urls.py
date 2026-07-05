"""Rotas públicas do módulo financeiro."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .financial_viewsets import (
    ChargeViewSet,
    FinancialCategoryViewSet,
    MonthlySubscriptionViewSet,
)
from .transaction_viewset import TransactionViewSet

router = DefaultRouter()
router.register(r"categories", FinancialCategoryViewSet, basename="financial-category")
router.register(r"charges", ChargeViewSet, basename="charge")
router.register(r"subscriptions", MonthlySubscriptionViewSet, basename="subscription")
router.register(r"", TransactionViewSet, basename="transaction")

urlpatterns = [path("", include(router.urls))]
