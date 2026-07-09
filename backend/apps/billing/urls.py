from django.urls import path

from apps.billing.views import (
    AsaasWebhookView,
    CancelSubscriptionView,
    ChangePlanView,
    CreateSubscriptionView,
    CurrentSubscriptionView,
    PaymentListView,
    PlanListView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("subscription/me/", CurrentSubscriptionView.as_view(), name="billing-subscription-me"),
    path("subscription/create/", CreateSubscriptionView.as_view(), name="billing-subscription-create"),
    path("subscription/cancel/", CancelSubscriptionView.as_view(), name="billing-subscription-cancel"),
    path("subscription/change-plan/", ChangePlanView.as_view(), name="billing-subscription-change-plan"),
    path("payments/", PaymentListView.as_view(), name="billing-payments"),
    path("webhooks/asaas/", AsaasWebhookView.as_view(), name="billing-webhook-asaas"),
]
