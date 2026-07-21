from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.scheduling.api.v1.filters import PackageFilter, ScheduleBlockFilter
from apps.scheduling.api.v1.serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    PackageSessionSerializer,
    PatientPackageSerializer,
    RoomSerializer,
    ScheduleBlockSerializer,
)
from apps.scheduling.exceptions import CompletedPackageSessionRemovalError
from apps.scheduling.selectors.resources import (
    package_sessions_queryset,
    patient_packages_queryset,
    rooms_queryset,
    schedule_blocks_queryset,
)
from apps.scheduling.services.package_sessions import (
    cancel_patient_package,
    remove_package_session,
)

from .base import ScopedAgendaMixin


class ScheduleBlockViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = ScheduleBlockSerializer
    filterset_class = ScheduleBlockFilter

    def get_queryset(self):
        return self.scope_queryset(schedule_blocks_queryset())

    def perform_create(self, serializer):
        item = serializer.save(organization=self.request.organization)
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
        return self.scope_queryset(rooms_queryset())


class PatientPackageViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = PatientPackageSerializer
    filterset_class = PackageFilter
    ordering_fields = ["created_at", "valid_until", "sessions_used"]

    def get_queryset(self):
        return self.scope_queryset(patient_packages_queryset())

    def perform_create(self, serializer):
        package = serializer.save(organization=self.request.organization)
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
        serializer = AppointmentCreateSerializer(
            data=payload,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save(
            organization=package.organization,
            created_by=request.user,
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            package,
            "Sessão adicionada ao pacote",
        )
        return Response(
            AppointmentDetailSerializer(
                appointment,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        package = cancel_patient_package(
            actor=request.user,
            package=self.get_object(),
        )
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
            "sessions_contracted": request.data.get(
                "sessions_contracted",
                current.sessions_contracted,
            ),
            "total_value": request.data.get("total_value", current.total_value),
            "valid_from": request.data.get("valid_from", timezone.localdate()),
            "valid_until": request.data.get("valid_until"),
            "generate_charge": request.data.get("generate_charge", False),
        }
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        renewed = serializer.save(
            organization=current.organization,
            created_by=request.user,
        )
        log_access(request, AuditLog.Action.CREATE, renewed, "Pacote renovado")
        return Response(
            self.get_serializer(renewed).data,
            status=status.HTTP_201_CREATED,
        )


class PackageSessionViewSet(ScopedAgendaMixin, viewsets.ModelViewSet):
    serializer_class = PackageSessionSerializer

    def get_queryset(self):
        return self.scope_queryset(
            package_sessions_queryset(),
            therapist_field="package__therapist",
        )

    def destroy(self, request, *args, **kwargs):
        item = self.get_object()
        try:
            package = remove_package_session(
                actor=request.user,
                package_session=item,
            )
        except CompletedPackageSessionRemovalError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        log_access(
            request,
            AuditLog.Action.DELETE,
            package,
            "Sessão removida do pacote",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
