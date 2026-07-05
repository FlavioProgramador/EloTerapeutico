"""Fluxos de cobrança vinculados a sessões concluídas."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from ..models import Charge
from ..services.charges import create_charge, eligible_sessions, generate_monthly_charges
from .serializers import (
    ChargeCreateSerializer,
    ChargeDetailSerializer,
    ChargeListSerializer,
    EligibleAppointmentSerializer,
    GenerateMonthlyChargesSerializer,
)
from .views import FinancialPermission


def _service_call(callable_, **kwargs):
    try:
        return callable_(**kwargs)
    except DjangoValidationError as exc:
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        raise ValidationError(detail) from exc


class ChargeViewSet(viewsets.ModelViewSet):
    permission_classes = [FinancialPermission]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if not user.is_therapist:
            return Charge.objects.none()
        return Charge.objects.filter(therapist=user).select_related(
            "patient", "professional", "transaction"
        ).prefetch_related("items__appointment")

    def get_serializer_class(self):
        if self.action == "create":
            return ChargeCreateSerializer
        if self.action == "retrieve":
            return ChargeDetailSerializer
        return ChargeListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        charge = _service_call(
            create_charge,
            therapist=request.user,
            actor=request.user,
            patient_id=data["patient"].pk,
            appointment_ids=data["appointment_ids"],
            due_date=data["due_date"],
            payment_link=data.get("payment_link", ""),
            notes=data.get("notes", ""),
            description=data.get("description", ""),
        )
        payload = ChargeDetailSerializer(charge, context={"request": request}).data
        return Response(payload, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="eligible-sessions")
    def eligible_appointments(self, request):
        if not request.user.is_therapist:
            raise ValidationError("Somente o profissional responsável pode listar sessões.")
        queryset = eligible_sessions(
            therapist=request.user,
            patient_id=request.query_params.get("patient"),
            start_date=request.query_params.get("start_date"),
            end_date=request.query_params.get("end_date"),
        )
        return Response(EligibleAppointmentSerializer(queryset, many=True).data)

    @action(detail=False, methods=["post"], url_path="generate-monthly")
    def generate_monthly(self, request):
        serializer = GenerateMonthlyChargesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.is_therapist:
            raise ValidationError("Somente o profissional responsável pode gerar cobranças.")
        generated, errors = _service_call(
            generate_monthly_charges,
            therapist=request.user,
            actor=request.user,
            **serializer.validated_data,
        )
        return Response(
            {
                "generated_count": len(generated),
                "charge_ids": [item.pk for item in generated],
                "errors": errors,
            },
            status=status.HTTP_201_CREATED if generated else status.HTTP_200_OK,
        )
