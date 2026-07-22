from __future__ import annotations

import json
import urllib.request

import pytest
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.users.models import AuthSession, User
from apps.users.services.sessions import issue_token_pair

pytestmark = pytest.mark.django_db(transaction=True)


def test_logout_completes_over_real_http(live_server):
    user = User.objects.create_user(
        email="logout-live-http@example.test",
        full_name="Logout HTTP",
        password="TestPass2026!_http",
        role=User.Role.THERAPIST,
    )
    tokens = issue_token_pair(user=user)
    session = AuthSession.objects.get(user=user)
    request = urllib.request.Request(
        f"{live_server.url}/api/v1/auth/logout/",
        data=json.dumps({"refresh": tokens["refresh"]}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        assert response.status == 200
        payload = json.loads(response.read())

    session.refresh_from_db()
    assert payload["message"] == "Logout realizado com sucesso."
    assert session.revoked_at is not None
    assert BlacklistedToken.objects.filter(token__jti=session.refresh_jti).exists()
