from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import AuditLog, log_access

from apps.agenda.api.filters import PackageFilter, ScheduleBlockFilter
from apps.agenda.models import Appointment, PackageSession, PatientPackage, Room, ScheduleBlock
from apps.agenda.api.serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    PackageSessionSerializer,
    PatientPackageSerializer,
    RoomSerializer,
    ScheduleBlockSerializer,
)
from .base import ScopedAgendaMixin


class ScheduleBlockViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = ScheduleBlockSerializer
    filterset_class = ScheduleBlockFilter

    def get_queryset(self):
        return self.scope_queryset(ScheduleBlock.objects.select_related("therapist", "created_by"))

    def perform_create(self, serializer):
        item = serializer.save()
        log_access(
            self.request,
            AuditLog.Action.CREATE,
            item,
            "Bloqueio de horário criado",
        )

    def perform_update(self, serializer):
        item = serializer.save()
        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            item,
            "Bloqueio de horário atualizado",
        )

    def perform_destroy(self, instance):
        log_access(
            self.request,
            AuditLog.Action.DELETE,
            instance,
            "Bloqueio de horário removido",
        )
        instance.delete()


class RoomViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    pagination_class = None

    def get_queryset(self):
        return self.scope_queryset(Room.objects.all())


class PatientPackageViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = PatientPackageSerializer
    filterset_class = PackageFilter
    ordering_fields = ["created_at", "valid_until", "sessions_used"]

    def get_queryset(self):
        queryset = PatientPackage.objects.select_related("patient", "therapist", "created_by").prefetch_related(
            "package_sessions__appointment"
        )
        return self.scope_queryset(queryset)

    def perform_create(self, serializer):
        package = serializer.save()
        log_access(self.request, AuditLog.Action.CREATE, package, "Pacote criado")

    def perform_update(self, serializer):
        package = serializer.save()
        log_access(self.request, AuditLog.Action.UPDATE, package, "Pacote atualizado")

    @action(detail=True, methods=["post"], url_path="add-session")
    def add_session(self, request, pk=None):
        package = self.get_object()
        payload = {
            **request.data,
            "patient": package.patient_id,
            "therapist": package.therapist_id,
            "package": package.id,
        }
        serializer = AppointmentCreateSerializer(data=payload, context={"request": request})
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            package,
            "Sessão adicionada ao pacote",
        )
        return Response(
            AppointmentDetailSerializer(appointment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        package = self.get_object()
        package.status = PatientPackage.Status.CANCELLED
        package.save(update_fields=["status", "updated_at"])
        for appointment in package.appointments.filter(
            start_time__gte=timezone.now(),
            status__in=[
                Appointment.Status.SCHEDULED,
                Appointment.Status.CONFIRMED,
            ],
        ):
            appointment.status = Appointment.Status.CANCELLED
            appointment.cancellation_reason = "Pacote cancelado."
            appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])
        log_access(request, AuditLog.Action.UPDATE, package, "Pacote cancelado")
        return Response(self.get_serializer(package).data)

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        current = self.get_object()
        payload = {
            "patient": current.patient_id,
            "therapist": current.therapist_id,
            "name": request.data.get("name", f"Renovação - {current.name}"),
            "description": request.data.get("description", current.description),
            "sessions_contracted": request.data.get("sessions_contracted", current.sessions_contracted),
            "total_value": request.data.get("total_value", current.total_value),
            "valid_from": request.data.get("valid_from", timezone.localdate()),
            "valid_until": request.data.get("valid_until"),
            "generate_charge": request.data.get("generate_charge", False),
        }
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        renewed = serializer.save()
        log_access(request, AuditLog.Action.CREATE, renewed, "Pacote renovado")
        return Response(
            self.get_serializer(renewed).data,
            status=status.HTTP_201_CREATED,
        )


class PackageSessionViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = PackageSessionSerializer

    def get_queryset(self):
        queryset = PackageSession.objects.select_related("package", "package__therapist", "appointment")
        return self.scope_queryset(queryset, therapist_field="package__therapist")

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        if item.status == PackageSession.Status.COMPLETED:
            return Response(
                {"detail": "Sessões realizadas não podem ser removidas."},
                status=status.HTTP_409_CONFLICT,
            )
        if item.appointment:
            item.appointment.status = Appointment.Status.CANCELLED
            item.appointment.cancellation_reason = "Sessão removida do pacote."
            item.appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])
        if item.consumed:
            item.package.release()
        log_access(
            request,
            AuditLog.Action.DELETE,
            item.package,
            "Sessão removida do pacote",
        )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
