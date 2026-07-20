"""Endpoint de geração de cobranças por consulta."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import (
    AppointmentChargeGenerationSerializer,
)
from apps.finances.services import generate_appointment_charges


class AppointmentChargeActionsMixin:
    @action(detail=False, methods=["post"], url_path="generate-monthly-charges")
    def generate_monthly_charges(self, request):
        serializer = AppointmentChargeGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = generate_appointment_charges(
            actor=request.user, **serializer.validated_data
        )
        return Response(result.as_dict(), status=status.HTTP_201_CREATED)
