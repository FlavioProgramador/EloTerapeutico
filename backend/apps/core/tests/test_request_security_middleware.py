from __future__ import annotations

import re

from django.test import TestCase, override_settings


class RequestSecurityMiddlewareTests(TestCase):
    def test_preserves_valid_request_id_and_returns_it_to_the_client(self):
        response = self.client.get("/health/live/", HTTP_X_REQUEST_ID="request-123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "request-123")

    def test_replaces_invalid_request_id_with_generated_identifier(self):
        response = self.client.get(
            "/health/live/",
            HTTP_X_REQUEST_ID="invalid request id with spaces and sensitive text",
        )

        request_id = response.headers["X-Request-ID"]
        self.assertRegex(request_id, re.compile(r"^[a-f0-9]{32}$"))

    def test_adds_defensive_headers_without_overwriting_view_headers(self):
        response = self.client.get("/health/live/")

        self.assertEqual(
            response.headers["Permissions-Policy"],
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
        )
        self.assertEqual(response.headers["Cross-Origin-Resource-Policy"], "same-site")
        self.assertEqual(response.headers["X-Permitted-Cross-Domain-Policies"], "none")

    @override_settings(SECURITY_CONTENT_SECURITY_POLICY="default-src 'self'; object-src 'none'")
    def test_adds_configured_content_security_policy(self):
        response = self.client.get("/health/live/")

        self.assertEqual(
            response.headers["Content-Security-Policy"],
            "default-src 'self'; object-src 'none'",
        )
