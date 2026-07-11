from django.urls import path

from apps.billing.access_views import EntitlementStatusView
from apps.billing.views import (
    AsaasWebhookView,
    BillingIntegrationHealthView,
    BillingOrderDetailView,
    BillingOrderListView,
    CancelSubscriptionView,
    ChangePlanView,
    CheckoutCreateView,
    CheckoutPreviewView,
    CreateSubscriptionView,
    CurrentSubscriptionView,
    PaymentDetailView,
    PaymentListView,
    PaymentRefreshView,
    PaymentSummaryView,
    PlanListView,
    PlanPriceListView,
    ResumeSubscriptionView,
    ScheduleCancellationView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("plan-prices/", PlanPriceListView.as_view(), name="billing-plan-prices"),
    path("entitlement/", EntitlementStatusView.as_view(), name="billing-entitlement"),
    path("checkout/preview/", CheckoutPreviewView.as_view(), name="billing-checkout-preview"),
    path("checkout/create/", CheckoutCreateView.as_view(), name="billing-checkout-create"),
    path("subscription/me/", CurrentSubscriptionView.as_view(), name="billing-subscription-me"),
    path("subscription/create/", CreateSubscriptionView.as_view(), name="billing-subscription-create"),
    path("subscription/cancel/", CancelSubscriptionView.as_view(), name="billing-subscription-cancel"),
    path(
        "subscription/cancel-at-period-end/",
        ScheduleCancellationView.as_view(),
        name="billing-subscription-cancel-at-period-end",
    ),
    path("subscription/resume/", ResumeSubscriptionView.as_view(), name="billing-subscription-resume"),
    path("subscription/change-plan/", ChangePlanView.as_view(), name="billing-subscription-change-plan"),
    path("orders/", BillingOrderListView.as_view(), name="billing-orders"),
    path("orders/<uuid:public_id>/", BillingOrderDetailView.as_view(), name="billing-order-detail"),
    path("payments/", PaymentListView.as_view(), name="billing-payments"),
    path("payments/summary/", PaymentSummaryView.as_view(), name="billing-payments-summary"),
    path("payments/<int:pk>/", PaymentDetailView.as_view(), name="billing-payment-detail"),
    path("payments/<int:pk>/refresh/", PaymentRefreshView.as_view(), name="billing-payment-refresh"),
    path("integrations/asaas/health/", BillingIntegrationHealthView.as_view(), name="billing-asaas-health"),
    path("webhooks/asaas/", AsaasWebhookView.as_view(), name="billing-webhook-asaas"),
]
