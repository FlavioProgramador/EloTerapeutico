from unittest.mock import MagicMock, patch

from django.test import TestCase


class HealthCheckTests(TestCase):
    def test_liveness_does_not_depend_on_external_services(self):
        response = self.client.get("/health/live/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    @patch("apps.core.health.redis.Redis.from_url")
    def test_readiness_checks_database_and_redis(self, from_url):
        client = MagicMock()
        client.ping.return_value = True
        from_url.return_value = client

        response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"], {"database": "ok", "redis": "ok"})
        client.close.assert_called_once()

    @patch("apps.core.health.redis.Redis.from_url")
    def test_readiness_returns_503_when_redis_is_unavailable(self, from_url):
        from_url.side_effect = ConnectionError("indisponível")

        response = self.client.get("/health/ready/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["redis"], "error")
