from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from apps.audit.integrations import AuditLogMixin
from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.scheduling.api.v1.filters import AppointmentFilter
from apps.scheduling.api.v1.serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
    CheckAvailabilitySerializer,
)
from apps.scheduling.exceptions import CompletedAppointmentDeletionError
from apps.scheduling.models import Appointment
from apps.scheduling.selectors import appointment_queryset
from apps.scheduling.selectors.users import get_accessible_therapist
from apps.scheduling.services import (
    cancel_appointment_for_deletion,
    update_appointment_status,
)
from apps.scheduling.services.exports import build_appointments_csv

from .base import ScopedAgendaMixin


def _validation_detail(exc: DjangoValidationError):
    return getattr(exc, "message_dict", None) or getattr(exc, "messages", [str(exc)])


class AppointmentViewSet(AuditLogMixin, ScopedAgendaMixin, viewsets.ModelViewSet):
    filterset_class = AppointmentFilter
    ordering_fields = ["start_time", "status", "session_value", "created_at"]
    ordering = ["start_time"]

    def get_queryset(self):
        include_details = self.action not in ["list", "today", "export"]
        return self.scope_queryset(
            appointment_queryset(include_details=include_details)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        if self.action in {"update", "partial_update", "reschedule"}:
            return AppointmentUpdateSerializer
        if self.action in {
            "update_status",
            "confirm",
            "cancel",
            "complete",
            "mark_no_show",
        }:
            return AppointmentStatusUpdateSerializer
        if self.action == "list":
            return AppointmentListSerializer
        return AppointmentDetailSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
        self._record_instance(AuditLog.Action.UPDATE, serializer.instance, on_commit=True)

    def destroy(self, request, *args, **kwargs):
        appointment = self.get_object()
        try:
            appointment = cancel_appointment_for_deletion(
                actor=request.user,
                appointment=appointment,
            )
        except CompletedAppointmentDeletionError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
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
        serializer = self.get_serializer(
            appointment,
            data=request.data,
            partial=True,
        )
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
        try:
            appointment = update_appointment_status(
                actor=self.request.user,
                appointment=serializer.instance,
                validated_data=dict(serializer.validated_data),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(_validation_detail(exc)) from exc
        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            appointment,
            f"Status da consulta alterado para {new_status}",
        )
        return Response(
            AppointmentDetailSerializer(
                appointment,
                context={"request": self.request},
            ).data
        )

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
        log_access(request, AuditLog.Action.UPDATE, appointment, "Consulta remarcada")
        return Response(
            AppointmentDetailSerializer(
                appointment,
                context={"request": request},
            ).data
        )

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
        serializer = CheckAvailabilitySerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        therapist = get_accessible_therapist(
            actor=request.user,
            therapist_id=serializer.validated_data.get("therapist_id"),
        )
        return Response(
            serializer.get_available_slots(
                therapist,
                serializer.validated_data,
            )
        )

    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset()).order_by("start_time")
        content = build_appointments_csv(appointments=queryset)
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="agenda.csv"'
        log_access(request, AuditLog.Action.EXPORT, obj_repr="Agenda exportada")
        return response
