"""Compatibilidade para imports antigos das views de billing.

Novos imports devem utilizar ``apps.billing.api.v1.views``.
"""

from .api.v1.views import (
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
    EntitlementStatusView,
    PaymentDetailView,
    PaymentListView,
    PaymentRefreshView,
    PaymentSummaryView,
    PlanListView,
    PlanPriceListView,
    ResumeSubscriptionView,
    ScheduleCancellationView,
)
from .api.v1.views.common import (
    checkout_response_payload as _checkout_response_payload,
)
from .api.v1.views.common import (
    gateway_error_response as _gateway_error_response,
)
from .api.v1.views.common import (
    public_checkout_data as _public_checkout_data,
)
from .api.v1.views.common import (
    service_checkout_data as _service_checkout_data,
)
from .api.v1.views.common import (
    validation_error_response as _validation_error_response,
)

__all__ = [
    "AsaasWebhookView",
    "BillingIntegrationHealthView",
    "BillingOrderDetailView",
    "BillingOrderListView",
    "CancelSubscriptionView",
    "ChangePlanView",
    "CheckoutCreateView",
    "CheckoutPreviewView",
    "CreateSubscriptionView",
    "CurrentSubscriptionView",
    "EntitlementStatusView",
    "PaymentDetailView",
    "PaymentListView",
    "PaymentRefreshView",
    "PaymentSummaryView",
    "PlanListView",
    "PlanPriceListView",
    "ResumeSubscriptionView",
    "ScheduleCancellationView",
    "_checkout_response_payload",
    "_gateway_error_response",
    "_public_checkout_data",
    "_service_checkout_data",
    "_validation_error_response",
]
