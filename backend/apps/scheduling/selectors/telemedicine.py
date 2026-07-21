"""Selectors de acesso a salas de telemedicina."""

from django.shortcuts import get_object_or_404

from apps.scheduling.models import TelemedicineRoom


def get_telemedicine_room_by_token(*, role: str, token):
    token_field = "patient_token" if role == "patient" else "professional_token"
    return get_object_or_404(
        TelemedicineRoom.objects.select_related(
            "organization",
            "appointment",
            "appointment__patient",
            "appointment__therapist",
        ),
        **{token_field: token},
    )


__all__ = ["get_telemedicine_room_by_token"]
