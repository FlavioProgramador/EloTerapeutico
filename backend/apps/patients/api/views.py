"""
apps/patients/views.py
Views/ViewSets para o app de Pacientes.
"""

from django.db import models
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import PatientFilter
from .models import Patient
from .serializers import (
    PatientCreateUpdateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
)


class PatientPermission(IsAuthenticated):
    """Permissões por função e vínculo com o terapeuta responsável."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        user = request.user
        if user.is_admin_role or user.is_therapist:
            return True
        if user.is_secretary:
            return request.method in ["GET", "HEAD", "OPTIONS", "POST"]
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role:
            return True
        if user.is_secretary:
            return request.method in ["GET", "HEAD", "OPTIONS"]
        return obj.therapist == user


class PatientViewSet(viewsets.ModelViewSet):
    """Gerenciamento de pacientes com isolamento por profissional."""

    permission_classes = [PatientPermission]
    filterset_class = PatientFilter
    ordering_fields = ["full_name", "created_at", "birth_date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Patient.objects.none()

        manager = Patient.all_objects if self.action == "restore" else Patient.objects
        if user.is_admin_role or user.is_secretary:
            return manager.all().order_by("full_name")
        return manager.filter(therapist=user).order_by("full_name")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PatientCreateUpdateSerializer
        if self.action == "list":
            return PatientListSerializer
        return PatientDetailSerializer

    def perform_create(self, serializer):
        if self.request.user.is_therapist:
            serializer.save(therapist=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """DELETE arquiva o cadastro por exclusão lógica."""
        instance.soft_delete()

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Encerra o acompanhamento sem classificar o cadastro como arquivado."""
        patient = self.get_object()
        if not patient.is_active:
            return Response(
                {"detail": "Paciente já está desativado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient.status = Patient.Status.INACTIVE
        patient.is_active = False
        patient.deleted_at = timezone.now()
        patient.save(
            update_fields=["status", "is_active", "deleted_at", "updated_at"]
        )
        return Response(
            {"detail": "Paciente desativado com sucesso."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """Restaura um paciente anteriormente desativado ou arquivado."""
        patient = self.get_object()
        if patient.is_active:
            return Response(
                {"detail": "Paciente já está ativo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        patient.restore()
        return Response(
            {"detail": "Paciente restaurado com sucesso."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        """Retorna um resumo administrativo do paciente."""
        patient = self.get_object()

        appointment_count = 0
        last_session_date = None
        try:
            from apps.agenda.models import Appointment

            appointments_qs = Appointment.objects.filter(patient=patient)
            appointment_count = appointments_qs.count()
            last_appointment = appointments_qs.filter(
                status="confirmed",
                start_time__lte=timezone.now(),
            ).order_by("-start_time").first()
            if last_appointment:
                last_session_date = last_appointment.start_time
        except ImportError:
            pass

        total_paid = 0
        try:
            from apps.financeiro.models import FinancialTransaction

            total_paid = FinancialTransaction.objects.filter(
                patient=patient,
                transaction_type="income",
                payment_status="paid",
            ).aggregate(total=models.Sum("amount"))["total"] or 0
        except ImportError:
            pass

        return Response(
            {
                "appointment_count": appointment_count,
                "last_session_date": last_session_date,
                "total_paid": float(total_paid),
            },
            status=status.HTTP_200_OK,
        )
