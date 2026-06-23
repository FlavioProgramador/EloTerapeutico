"""
apps/patients/views.py
Views/ViewSets para o app de Pacientes.
"""

from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Patient
from .filters import PatientFilter
from .serializers import (
    PatientListSerializer,
    PatientDetailSerializer,
    PatientCreateUpdateSerializer,
)


class PatientPermission(IsAuthenticated):
    """
    Classe de permissão personalizada para o ViewSet de Pacientes.
    - Admin: Acesso total.
    - Secretária: Apenas leitura (Safe Methods) e criação. Não pode editar nem deletar.
    - Terapeuta: Controle total sobre os pacientes vinculados a ele.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        user = request.user
        if user.is_admin_role or user.is_therapist:
            return True
        if user.is_secretary:
            # Secretária pode listar, detalhar e cadastrar pacientes. Não pode deletar.
            return request.method in ["GET", "HEAD", "OPTIONS", "POST"]
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role:
            return True
        if user.is_secretary:
            # Secretária apenas visualiza dados cadastrais
            return request.method in ["GET", "HEAD", "OPTIONS"]
        # Terapeuta só acessa se for o dono (responsável)
        return obj.therapist == user


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Pacientes.
    """
    permission_classes = [PatientPermission]
    filterset_class = PatientFilter
    ordering_fields = ["full_name", "created_at", "birth_date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Patient.objects.none()

        # Para ação de restauração, precisamos listar também os pacientes excluídos
        if self.action == "restore":
            manager = Patient.all_objects
        else:
            manager = Patient.objects

        if user.is_admin_role or user.is_secretary:
            return manager.all()
        return manager.filter(therapist=user)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PatientCreateUpdateSerializer
        if self.action == "list":
            return PatientListSerializer
        return PatientDetailSerializer

    def perform_create(self, serializer):
        # Se for terapeuta criando, auto-vincula a si mesmo
        # Se for admin/secretaria, deve especificar o terapeuta no payload
        if self.request.user.is_therapist:
            serializer.save(therapist=self.request.user)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        # Executa soft delete ao invés de delete físico
        instance.soft_delete()

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """
        Ação personalizada para desativar (soft delete) o paciente.
        POST /api/v1/patients/{id}/deactivate/
        """
        patient = self.get_object()
        if not patient.is_active:
            return Response(
                {"detail": "Paciente já está desativado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        patient.soft_delete()
        return Response(
            {"detail": "Paciente desativado com sucesso."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """
        Ação personalizada para restaurar um paciente desativado.
        POST /api/v1/patients/{id}/restore/
        """
        patient = self.get_object()
        if patient.is_active:
            return Response(
                {"detail": "Paciente já está ativo."},
                status=status.HTTP_400_BAD_REQUEST
            )
        patient.restore()
        return Response(
            {"detail": "Paciente restaurado com sucesso."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        """
        Retorna informações resumidas sobre o histórico de consultas e faturamento do paciente.
        GET /api/v1/patients/{id}/summary/
        """
        patient = self.get_object()
        
        # Obter contagem de consultas e data da última sessão
        appointment_count = 0
        last_session_date = None
        try:
            from apps.agenda.models import Appointment
            appointments_qs = Appointment.objects.filter(patient=patient)
            appointment_count = appointments_qs.count()
            last_appointment = appointments_qs.filter(
                status="confirmed",
                start_time__lte=timezone.now()
            ).order_by("-start_time").first()
            if last_appointment:
                last_session_date = last_appointment.start_time
        except ImportError:
            pass

        # Obter total pago pelo paciente
        total_paid = 0
        try:
            from apps.financeiro.models import FinancialTransaction
            total_paid = FinancialTransaction.objects.filter(
                patient=patient,
                transaction_type="income",
                payment_status="paid"
            ).aggregate(total=models.Sum("amount"))["total"] or 0
        except ImportError:
            pass

        return Response({
            "appointment_count": appointment_count,
            "last_session_date": last_session_date,
            "total_paid": float(total_paid),
        }, status=status.HTTP_200_OK)
