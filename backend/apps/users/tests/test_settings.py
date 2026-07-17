from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.users.models import PracticeSettings, User

pytestmark = pytest.mark.django_db


def make_user(email: str) -> User:
    return User.objects.create_user(
        email=email,
        password="SenhaForte123!",
        full_name="Profissional Teste",
        role=User.Role.THERAPIST,
    )


def test_user_updates_only_own_practice_settings():
    owner = make_user("settings-owner@example.test")
    other = make_user("settings-other@example.test")
    other_settings = PracticeSettings.objects.create(user=other, trade_name="Outro consultório")
    client = APIClient()
    client.force_authenticate(owner)

    response = client.patch(
        reverse("user-settings"),
        {
            "trade_name": "Consultório Elo",
            "appointment_interval_minutes": 10,
            "minimum_booking_notice_hours": 2,
            "internal_communications_enabled": True,
        },
        format="json",
    )

    assert response.status_code == 200
    settings = PracticeSettings.objects.get(user=owner)
    assert settings.trade_name == "Consultório Elo"
    assert settings.appointment_interval_minutes == 10
    other_settings.refresh_from_db()
    assert other_settings.trade_name == "Outro consultório"


def test_quiet_hours_require_start_and_end():
    user = make_user("settings-quiet@example.test")
    client = APIClient()
    client.force_authenticate(user)

    response = client.patch(
        reverse("user-settings"),
        {"quiet_hours_enabled": True},
        format="json",
    )

    assert response.status_code == 400


def test_profile_exposes_and_updates_new_preferences():
    user = make_user("settings-profile@example.test")
    client = APIClient()
    client.force_authenticate(user)

    response = client.patch(
        reverse("user-me"),
        {
            "display_name": "Dra. Elo",
            "profession": "Psicóloga",
            "default_modality": "online",
            "timezone": "America/Sao_Paulo",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["display_name"] == "Dra. Elo"
    user.refresh_from_db()
    assert user.default_modality == "online"
