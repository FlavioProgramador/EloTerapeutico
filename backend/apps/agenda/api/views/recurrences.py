from datetime import datetime, timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.agenda.api.filters import RecurrenceFilter
from apps.agenda.api.serializers import (
    AppointmentDetailSerializer,
    AppointmentRecurrenceSerializer,
    AppointmentUpdateSerializer,
)
from apps.agenda.models import Appointment, AppointmentRecurrence, Room
from apps.audit.services.access_logging import AuditLog, log_access

from .base import ScopedAgendaMixin


def _as_time(value):
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    return value


class AppointmentRecurrenceViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = AppointmentRecurrenceSerializer
    filterset_class = RecurrenceFilter
    ordering_fields = ["created_at", "starts_on", "ends_on"]

    def get_queryset(self):
        queryset = AppointmentRecurrence.objects.select_related("patient", "therapist", "room").prefetch_related(
            "appointments"
        )
        return self.scope_queryset(queryset)

    def perform_create(self, serializer):
        recurrence = serializer.save(created_by=self.request.user)
        log_access(self.request, AuditLog.Action.CREATE, recurrence, "Recorrência criada")

    def perform_update(self, serializer):
        recurrence = serializer.save()
        log_access(self.request, AuditLog.Action.UPDATE, recurrence, "Recorrência atualizada")

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        return self._set_status(request, self.get_object(), AppointmentRecurrence.Status.PAUSED)

    @action(detail=True, methods=["post"])
    def reactivate(self, request, pk=None):
        return self._set_status(request, self.get_object(), AppointmentRecurrence.Status.ACTIVE)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        recurrence = self.get_object()
        recurrence.status = AppointmentRecurrence.Status.ENDED
        recurrence.ends_on = request.data.get("ends_on") or timezone.localdate()
        recurrence.save(update_fields=["status", "ends_on", "updated_at"])
        recurrence.appointments.filter(
            start_time__date__gt=recurrence.ends_on,
            status__in=[
                Appointment.Status.SCHEDULED,
                Appointment.Status.CONFIRMED,
            ],
        ).update(
            status=Appointment.Status.CANCELLED,
            cancellation_reason="Recorrência encerrada.",
        )
        log_access(request, AuditLog.Action.UPDATE, recurrence, "Recorrência encerrada")
        return Response(self.get_serializer(recurrence).data)

    def _set_status(self, request, recurrence, value):
        recurrence.status = value
        recurrence.save(update_fields=["status", "updated_at"])
        log_access(request, AuditLog.Action.UPDATE, recurrence, f"Recorrência: {value}")
        return Response(self.get_serializer(recurrence).data)

    @action(detail=True, methods=["post"], url_path="apply-change")
    @transaction.atomic
    def apply_change(self, request, pk=None):
        recurrence = self.get_object()
        scope = request.data.get("scope")
        occurrence_id = request.data.get("occurrence_id")
        if scope not in {"occurrence", "following", "all"}:
            return Response(
                {"scope": "Escopo inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        occurrence = get_object_or_404(recurrence.appointments.select_for_update(), pk=occurrence_id)
        if scope == "occurrence":
            serializer = AppointmentUpdateSerializer(
                occurrence,
                data=request.data.get("changes", {}),
                partial=True,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            item = serializer.save(updated_by=request.user)
            log_access(
                request,
                AuditLog.Action.UPDATE,
                item,
                "Exceção de recorrência atualizada",
            )
            return Response(AppointmentDetailSerializer(item, context={"request": request}).data)

        changes = request.data.get("changes", {})
        target_rule = recurrence
        if scope == "following":
            target_rule = AppointmentRecurrence.objects.create(
                patient=recurrence.patient,
                therapist=recurrence.therapist,
                frequency=changes.get("frequency", recurrence.frequency),
                interval=changes.get("interval", recurrence.interval),
                weekdays=changes.get("weekdays", recurrence.weekdays),
                starts_on=occurrence.start_time.date(),
                ends_on=changes.get("ends_on", recurrence.ends_on),
                max_occurrences=recurrence.max_occurrences,
                start_time=_as_time(changes.get("start_time", recurrence.start_time)),
                duration_minutes=changes.get("duration_minutes", recurrence.duration_minutes),
                timezone_name=recurrence.timezone_name,
                modality=changes.get("modality", recurrence.modality),
                appointment_type=changes.get("appointment_type", recurrence.appointment_type),
                room_id=changes.get("room", recurrence.room_id),
                session_value=changes.get("session_value", recurrence.session_value),
                notes=changes.get("notes", recurrence.notes),
                created_by=request.user,
            )
            recurrence.ends_on = occurrence.start_time.date() - timedelta(days=1)
            recurrence.save(update_fields=["ends_on", "updated_at"])

        editable = recurrence.appointments.select_for_update().filter(
            status__in=[
                Appointment.Status.SCHEDULED,
                Appointment.Status.CONFIRMED,
            ]
        )
        if scope == "following":
            editable = editable.filter(start_time__gte=occurrence.start_time)

        for item in editable:
            local = timezone.localtime(item.start_time)
            new_time = _as_time(changes.get("start_time"))
            effective_time = new_time or target_rule.start_time
            new_start = local.replace(
                hour=effective_time.hour,
                minute=effective_time.minute,
                second=0,
                microsecond=0,
            )
            duration = int(changes.get("duration_minutes", target_rule.duration_minutes))
            room_id = changes.get("room", target_rule.room_id)
            conflicts = Appointment.conflict_details(
                therapist=target_rule.therapist,
                patient=target_rule.patient,
                start_time=new_start,
                end_time=new_start + timedelta(minutes=duration),
                room=Room.objects.filter(pk=room_id).first(),
                exclude_id=item.pk,
            )
            if any(conflicts.values()):
                transaction.set_rollback(True)
                return Response(
                    {"detail": (f"Conflito ao alterar ocorrência de {local:%d/%m/%Y}.")},
                    status=status.HTTP_409_CONFLICT,
                )
            item.start_time = new_start
            item.end_time = new_start + timedelta(minutes=duration)
            item.room_id = room_id
            item.modality = changes.get("modality", target_rule.modality)
            item.appointment_type = changes.get("appointment_type", target_rule.appointment_type)
            item.recurrence = target_rule
            item.updated_by = request.user
            item.save()

        for field in [
            "frequency",
            "interval",
            "weekdays",
            "ends_on",
            "duration_minutes",
            "modality",
            "appointment_type",
            "session_value",
            "notes",
        ]:
            if field in changes:
                setattr(target_rule, field, changes[field])
        if "start_time" in changes:
            target_rule.start_time = _as_time(changes["start_time"])
        if "room" in changes:
            target_rule.room_id = changes["room"]
        target_rule.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            target_rule,
            f"Recorrência alterada: {scope}",
        )
        return Response(self.get_serializer(target_rule).data)
