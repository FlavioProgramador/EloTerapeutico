from django.urls import path

from .views import AsaasWebhookView

urlpatterns = [
    path(
        "webhooks/asaas/",
        AsaasWebhookView.as_view(),
        name="billing-webhook-asaas",
    ),
]
