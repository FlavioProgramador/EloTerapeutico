import csv
from io import StringIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import AuditLog, AuditLogMixin, log_access

from ..filters import AppointmentFilter
from ..models import Appointment, PackageSession, TelemedicineRoom
from ..serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
    CheckAvailabilitySerializer,
)
from ..services import release_package_session, sync_package_session_status
from .base import ScopedAgendaMixin


class AppointmentViewSet(AuditLogMixin, ScopedAgendaMixin, viewsets.ModelViewSet):
    filterset_class = AppointmentFilter
    ordering_fields = ["start_time", "status", "session_value", "created_at"]
    ordering = ["start_time"]

    def get_queryset(self):
        queryset = Appointment.objects.select_related(
            "patient",
            "therapist",
            "room",
            "recurrence",
            "package",
            "telemedicine_room",
            "evolution",
            "evolution__clinical_data",
        )
        # Otimização: Evita prefetches pesados em listagens e exportações
        # que não utilizam participantes ou lembretes.
        if self.action not in ["list", "today", "export"]:
            queryset = queryset.prefetch_related("participants", "reminders")

        return self.scope_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        if self.action in {"update", "partial_update", "reschedule"}:
            return AppointmentUpdateSerializer
        if self.action in {"update_status", "confirm", "cancel", "complete", "mark_no_show"}:
            return AppointmentStatusUpdateSerializer
        if self.action == "list":
            return AppointmentListSerializer
        return AppointmentDetailSerializer

    def perform_create(self, serializer):
        super().perform_create(serializer)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        super().perform_update(serializer)

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()
        if appointment.status == Appointment.Status.COMPLETED:
            return Response(
                {"detail": "Consultas realizadas não podem ser excluídas."},
                status=status.HTTP_409_CONFLICT,
            )
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = "Cancelada por exclusão administrativa."
        appointment.updated_by = request.user
        appointment.save(update_fields=["status", "cancellation_reason", "updated_by", "updated_at"])
        release_package_session(appointment)
        self._cancel_financial_transaction(appointment)
        log_access(
            request,
            AuditLog.Action.DELETE,
            appointment,
            "Consulta cancelada por exclusão",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        serializer = self.get_serializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return self._save_status(serializer, request.data.get("status"))

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._transition(request, Appointment.Status.CONFIRMED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(
            request,
            Appointment.Status.CANCELLED,
            cancellation_reason=request.data.get("cancellation_reason", ""),
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._transition(request, Appointment.Status.COMPLETED)

    @action(detail=True, methods=["post"], url_path="mark-no-show")
    def mark_no_show(self, request, pk=None):
        return self._transition(request, Appointment.Status.MISSED)

    def _transition(self, request, new_status, **extra):
        appointment = self.get_object()
        serializer = AppointmentStatusUpdateSerializer(
            appointment,
            data={"status": new_status, **extra},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return self._save_status(serializer, new_status)

    def _save_status(self, serializer, new_status):
        appointment = serializer.save(updated_by=self.request.user)
        sync_package_session_status(appointment)
        if new_status == Appointment.Status.CONFIRMED:
            self._create_financial_transaction(appointment)
        elif new_status == Appointment.Status.CANCELLED:
            release_package_session(appointment)
            self._cancel_financial_transaction(appointment)
            try:
                appointment.telemedicine_room.revoke()
            except TelemedicineRoom.DoesNotExist:
                pass
        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            appointment,
            f"Status da consulta alterado para {new_status}",
        )
        return Response(AppointmentDetailSerializer(appointment, context={"request": self.request}).data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        serializer = AppointmentUpdateSerializer(
            appointment,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(
            status=Appointment.Status.SCHEDULED,
            origin=Appointment.Origin.RESCHEDULE,
            updated_by=request.user,
        )
        if hasattr(appointment, "package_session"):
            appointment.package_session.scheduled_for = appointment.start_time
            appointment.package_session.status = PackageSession.Status.RESCHEDULED
            appointment.package_session.save(update_fields=["scheduled_for", "status", "updated_at"])
        log_access(request, AuditLog.Action.UPDATE, appointment, "Consulta remarcada")
        return Response(AppointmentDetailSerializer(appointment, context={"request": request}).data)

    @action(detail=False, methods=["get"])
    def today(self, request):
        queryset = (
            self.filter_queryset(self.get_queryset())
            .filter(start_time__date=timezone.localdate())
            .order_by("start_time")
        )
        return Response(AppointmentListSerializer(queryset, many=True).data)

    @action(detail=False, methods=["post"], url_path="check-availability")
    def check_availability(self, request):
        serializer = CheckAvailabilitySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        therapist = request.user
        therapist_id = serializer.validated_data.get("therapist_id")
        if (request.user.is_admin_role or request.user.is_secretary) and therapist_id:
            from django.contrib.auth import get_user_model

            therapist = get_object_or_404(get_user_model(), pk=therapist_id, role="therapist")
        return Response(serializer.get_available_slots(therapist, serializer.validated_data))

    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by("start_time")
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Data",
                "Início",
                "Fim",
                "Paciente",
                "Profissional",
                "Modalidade",
                "Status",
                "Sala",
            ]
        )
        for item in queryset.iterator():
            local_start = timezone.localtime(item.start_time)
            local_end = timezone.localtime(item.end_time)
            writer.writerow(
                [
                    local_start.strftime("%d/%m/%Y"),
                    local_start.strftime("%H:%M"),
                    local_end.strftime("%H:%M"),
                    item.patient.display_name,
                    item.therapist.full_name,
                    item.get_modality_display(),
                    item.get_status_display(),
                    item.room.name if item.room else "Sem sala",
                ]
            )
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="agenda.csv"'
        log_access(request, AuditLog.Action.EXPORT, obj_repr="Agenda exportada")
        return response

    @staticmethod
    def _create_financial_transaction(appointment):
        from apps.financeiro.models import FinancialTransaction

        FinancialTransaction.objects.get_or_create(
            appointment=appointment,
            defaults={
                "therapist": appointment.therapist,
                "patient": appointment.patient,
                "transaction_type": FinancialTransaction.TransactionType.INCOME,
                "category": FinancialTransaction.Category.SESSION,
                "amount": appointment.session_value,
                "payment_method": FinancialTransaction.PaymentMethod.OTHER,
                "payment_status": FinancialTransaction.PaymentStatus.PENDING,
                "due_date": appointment.start_time.date(),
                "description": f"Consulta de {appointment.patient.display_name}",
            },
        )

    @staticmethod
    def _cancel_financial_transaction(appointment):
        from apps.financeiro.models import FinancialTransaction

        transaction_item = FinancialTransaction.objects.filter(
            appointment=appointment,
            payment_status=FinancialTransaction.PaymentStatus.PENDING,
        ).first()
        if transaction_item:
            transaction_item.cancel()
