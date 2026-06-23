"""
apps/agenda/views.py
Views e ViewSets para o app de Agenda.
"""

from datetime import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Appointment
from .filters import AppointmentFilter
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentStatusUpdateSerializer,
    CheckAvailabilitySerializer,
)


class AppointmentPermission(IsAuthenticated):
    """
    Permissões para acesso à agenda de consultas:
    - Admin e Secretária: Acesso total de leitura e escrita (para agendamento e gerenciamento da clínica).
    - Terapeuta: Acesso apenas às suas próprias consultas.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_admin_role or request.user.is_therapist or request.user.is_secretary

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role or user.is_secretary:
            return True
        return obj.therapist == user


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Consultas/Agendamentos.
    """
    permission_classes = [AppointmentPermission]
    filterset_class = AppointmentFilter
    ordering_fields = ["start_time", "status", "session_value"]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Appointment.objects.none()
        
        # Admin e secretária listam tudo
        if user.is_admin_role or user.is_secretary:
            return Appointment.objects.all().select_related("patient", "therapist")
            
        # Terapeutas listam apenas suas consultas
        return Appointment.objects.filter(therapist=user).select_related("patient", "therapist")

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        if self.action in ["update", "partial_update"]:
            return AppointmentUpdateSerializer
        if self.action == "update_status":
            return AppointmentStatusUpdateSerializer
        return AppointmentDetailSerializer

    def perform_create(self, serializer):
        # Cria a consulta principal
        therapist = self.request.user
        # Se for admin/secretaria, ela define o terapeuta no payload ou herda do serializer
        instance = serializer.save()
        
        # Cria recorrências se solicitado
        if instance.is_recurring:
            serializer.create_recurrences(instance, num_weeks=4)

        # Se criada como confirmada, dispara criação da transação financeira
        if instance.status == Appointment.Status.CONFIRMED:
            self._create_financial_transaction(instance)

    def perform_update(self, serializer):
        old_status = self.get_object().status
        instance = serializer.save()
        
        # Se o status mudou para confirmado nesta atualização
        if old_status != Appointment.Status.CONFIRMED and instance.status == Appointment.Status.CONFIRMED:
            self._create_financial_transaction(instance)
            
        # Se o status mudou de confirmado para cancelado, cancela a transação
        if old_status == Appointment.Status.CONFIRMED and instance.status == Appointment.Status.CANCELLED:
            self._cancel_financial_transaction(instance)

    def _create_financial_transaction(self, appointment):
        """
        Gera uma transação financeira pendente de receita (income)
        para a consulta que foi confirmada.
        """
        try:
            from apps.financeiro.models import FinancialTransaction
            # Evita duplicidade
            if not FinancialTransaction.objects.filter(appointment=appointment).exists():
                FinancialTransaction.objects.create(
                    therapist=appointment.therapist,
                    patient=appointment.patient,
                    appointment=appointment,
                    transaction_type="income",
                    category="session",
                    amount=appointment.session_value,
                    payment_method="other",
                    payment_status="pending",
                    due_date=appointment.start_time.date(),
                    description=f"Receita da consulta de {appointment.patient.full_name} realizada em {appointment.start_time.strftime('%d/%m/%Y')}"
                )
        except ImportError:
            pass

    def _cancel_financial_transaction(self, appointment):
        """
        Cancela a transação financeira caso o agendamento seja cancelado
        e o pagamento ainda esteja pendente.
        """
        try:
            from apps.financeiro.models import FinancialTransaction
            tx = FinancialTransaction.objects.filter(appointment=appointment).first()
            if tx and tx.payment_status == "pending":
                tx.payment_status = "cancelled"
                tx.save(update_fields=["payment_status", "updated_at"])
        except ImportError:
            pass

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        """
        Endpoint customizado para atualização rápida do status da consulta.
        PATCH /api/v1/agenda/appointments/{id}/status/
        """
        appointment = self.get_object()
        serializer = self.get_serializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_status = appointment.status
        self.perform_update(serializer)
        
        return Response(
            {
                "detail": "Status da consulta atualizado com sucesso.",
                "status": serializer.data.get("status")
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """
        Lista todas as consultas agendadas/confirmadas do terapeuta logado para o dia de hoje.
        GET /api/v1/agenda/appointments/today/
        """
        user = request.user
        today_start = timezone.localdate()
        today_end = today_start + timezone.timedelta(days=1)
        
        # Filtra queryset com base no usuário
        qs = Appointment.objects.filter(
            start_time__date=today_start,
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED]
        )
        
        if not user.is_admin_role and not user.is_secretary:
            qs = qs.filter(therapist=user)
            
        qs = qs.order_by("start_time")
        serializer = AppointmentListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="check-availability", permission_classes=[IsAuthenticated])
    def check_availability(self, request):
        """
        Verifica horários livres para agendamento em um determinado dia.
        POST /api/v1/agenda/appointments/check-availability/
        """
        serializer = CheckAvailabilitySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        therapist = request.user
        # Se for admin ou secretaria, o terapeuta deve ser especificado no payload
        # (adicionamos suporte para que possam pesquisar para outros terapeutas)
        therapist_id = request.data.get("therapist_id")
        if (request.user.is_admin_role or request.user.is_secretary) and therapist_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            therapist = get_object_or_404(User, id=therapist_id, role="therapist")
            
        slots = serializer.get_available_slots(therapist, serializer.validated_data)
        return Response(slots, status=status.HTTP_200_OK)
