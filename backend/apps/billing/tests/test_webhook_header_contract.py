from unittest.mock import MagicMock

from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase, override_settings

from apps.billing.services.gateways.asaas import AsaasGateway


@override_settings(ASAAS_WEBHOOK_TOKEN="official-webhook-token")
class WebhookHeaderContractTests(SimpleTestCase):
    def request(self, headers):
        request = MagicMock()
        request.headers = headers
        request.data = {"event": "PAYMENT_CREATED", "payment": {"id": "pay_header"}}
        return request

    def test_official_asaas_access_token_header_is_accepted(self):
        payload = AsaasGateway(require_api_key=False).parse_webhook(
            self.request({"asaas-access-token": "official-webhook-token"})
        )

        self.assertEqual(payload["event"], "PAYMENT_CREATED")

    def test_invalid_official_header_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            AsaasGateway(require_api_key=False).parse_webhook(
                self.request({"asaas-access-token": "invalid-token"})
            )

    def test_official_header_has_precedence_over_legacy_header(self):
        with self.assertRaises(PermissionDenied):
            AsaasGateway(require_api_key=False).parse_webhook(
                self.request(
                    {
                        "asaas-access-token": "invalid-token",
                        "X-Webhook-Token": "official-webhook-token",
                    }
                )
            )
