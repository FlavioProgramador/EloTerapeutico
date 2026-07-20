from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.scheduling.api.filters import RecurrenceFilter
from apps.scheduling.api.serializers import (
    AppointmentDetailSerializer,
    AppointmentRecurrenceSerializer,
    AppointmentUpdateSerializer,
)
from apps.scheduling.exceptions import InvalidRecurrenceScopeError, RecurrenceConflictError
from apps.scheduling.models import AppointmentRecurrence
from apps.scheduling.services import (
    apply_bulk_recurrence_change,
    end_recurrence,
    set_recurrence_status,
)

from .base import ScopedAgendaMixin


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
        raw_ends_on = request.data.get("ends_on")
        try:
            ends_on = date.fromisoformat(raw_ends_on) if raw_ends_on else None
        except (TypeError, ValueError):
            return Response({"ends_on": "Data final inválida."}, status=status.HTTP_400_BAD_REQUEST)
        recurrence = end_recurrence(recurrence=self.get_object(), ends_on=ends_on)
        log_access(request, AuditLog.Action.UPDATE, recurrence, "Recorrência encerrada")
        return Response(self.get_serializer(recurrence).data)

    def _set_status(self, request, recurrence, value):
        recurrence = set_recurrence_status(recurrence=recurrence, status=value)
        log_access(request, AuditLog.Action.UPDATE, recurrence, f"Recorrência: {value}")
        return Response(self.get_serializer(recurrence).data)

    @action(detail=True, methods=["post"], url_path="apply-change")
    def apply_change(self, request, pk=None):
        recurrence = self.get_object()
        scope = request.data.get("scope")
        occurrence_id = request.data.get("occurrence_id")
        if scope not in {"occurrence", "following", "all"}:
            return Response({"scope": "Escopo inválido."}, status=status.HTTP_400_BAD_REQUEST)
        occurrence = get_object_or_404(recurrence.appointments.all(), pk=occurrence_id)
        changes = request.data.get("changes", {})

        if scope == "occurrence":
            serializer = AppointmentUpdateSerializer(
                occurrence,
                data=changes,
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

        try:
            target_rule = apply_bulk_recurrence_change(
                actor=request.user,
                recurrence=recurrence,
                occurrence=occurrence,
                scope=scope,
                changes=changes,
            )
        except InvalidRecurrenceScopeError as exc:
            return Response({"scope": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except RecurrenceConflictError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        log_access(
            request,
            AuditLog.Action.UPDATE,
            target_rule,
            f"Recorrência alterada: {scope}",
        )
        return Response(self.get_serializer(target_rule).data)
