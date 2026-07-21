"""Endpoint de geração de cobranças por consulta."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import (
    AppointmentChargeGenerationSerializer,
)
from apps.finances.services import generate_appointment_charges
from apps.organizations.services.tenant_context import ensure_request_organization


class AppointmentChargeActionsMixin:
    @action(detail=False, methods=["post"], url_path="generate-monthly-charges")
    def generate_monthly_charges(self, request):
        serializer = AppointmentChargeGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization, _ = ensure_request_organization(
            request=request,
            required=True,
        )
        result = generate_appointment_charges(
            actor=request.user,
            organization=organization,
            **serializer.validated_data,
        )
        return Response(result.as_dict(), status=status.HTTP_201_CREATED)
