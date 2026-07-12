from django.test import TestCase, override_settings


@override_settings(
    CORS_ALLOW_ALL_ORIGINS=False,
    CORS_ALLOWED_ORIGINS=["http://localhost:3000"],
)
class CheckoutCorsTests(TestCase):
    endpoint = "/api/v1/billing/checkout/create/"

    def test_preflight_accepts_idempotency_header_for_allowed_origin(self):
        response = self.client.options(
            self.endpoint,
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                "authorization,content-type,idempotency-key"
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:3000",
        )
        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        self.assertIn("authorization", allowed_headers)
        self.assertIn("content-type", allowed_headers)
        self.assertIn("idempotency-key", allowed_headers)

    def test_preflight_does_not_authorize_unknown_origin(self):
        response = self.client.options(
            self.endpoint,
            HTTP_ORIGIN="https://origem-nao-autorizada.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                "authorization,content-type,idempotency-key"
            ),
        )

        self.assertNotEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "https://origem-nao-autorizada.example",
        )
