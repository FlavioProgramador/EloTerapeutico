from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.scheduling.api.v1.serializers import (
    AppointmentReminderSerializer,
    TelemedicineRoomSerializer,
)
from apps.scheduling.exceptions import TelemedicineUnavailableError
from apps.scheduling.selectors.resources import (
    appointment_reminders_queryset,
    telemedicine_rooms_queryset,
)
from apps.scheduling.selectors.telemedicine import get_telemedicine_room_by_token
from apps.scheduling.services.telemedicine import (
    cancel_appointment_reminder,
    open_telemedicine_room,
    regenerate_telemedicine_links,
)

from .base import ScopedAgendaMixin


class TelemedicineRoomViewSet(ScopedAgendaMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = TelemedicineRoomSerializer
    ordering = ["appointment__start_time"]

    def get_queryset(self):
        queryset = self.scope_queryset(
            telemedicine_rooms_queryset(),
            therapist_field="appointment__therapist",
        )
        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        date_value = self.request.query_params.get("date", "").strip()
        if search:
            queryset = queryset.filter(
                Q(appointment__patient__full_name__icontains=search)
                | Q(appointment__patient__social_name__icontains=search)
                | Q(appointment__therapist__full_name__icontains=search)
                | Q(appointment__appointment_type__icontains=search)
            )
        if status_value:
            queryset = queryset.filter(status=status_value)
        if date_value:
            queryset = queryset.filter(appointment__start_time__date=date_value)
        return queryset

    @action(detail=True, methods=["post"], url_path="regenerate-link")
    def regenerate_link(self, request, pk=None):
        room = regenerate_telemedicine_links(
            actor=request.user,
            room=self.get_object(),
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Links de telemedicina regenerados",
        )
        return Response(self.get_serializer(room).data)

    @action(detail=True, methods=["post"], url_path="open-room")
    def open_room(self, request, pk=None):
        try:
            room = open_telemedicine_room(
                actor=request.user,
                room=self.get_object(),
            )
        except TelemedicineUnavailableError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_410_GONE,
            )
        log_access(
            request,
            AuditLog.Action.VIEW,
            room.appointment,
            "Sala de telemedicina acessada",
        )
        data = self.get_serializer(room).data
        return Response({"professional_link": data["professional_link"]})


class AppointmentReminderViewSet(ScopedAgendaMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AppointmentReminderSerializer

    def get_queryset(self):
        return self.scope_queryset(
            appointment_reminders_queryset(),
            therapist_field="appointment__therapist",
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        reminder = cancel_appointment_reminder(
            actor=request.user,
            reminder=self.get_object(),
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            reminder.appointment,
            "Lembrete cancelado",
        )
        return Response(self.get_serializer(reminder).data)


class TelemedicineAccessView(APIView):
    """Valida tokens distintos de paciente e profissional."""

    permission_classes = [AllowAny]

    def get(self, request, role, token):
        if role not in {"patient", "professional"}:
            return Response(
                {"detail": "Papel inválido."},
                status=status.HTTP_404_NOT_FOUND,
            )
        room = get_telemedicine_room_by_token(role=role, token=token)
        if not room.is_accessible:
            return Response(
                {"detail": "A sala expirou ou foi revogada."},
                status=status.HTTP_410_GONE,
            )
        if role == "professional":
            user = request.user
            if not user.is_authenticated or not (
                user.is_admin_role
                or user.is_secretary
                or user.id == room.appointment.therapist_id
            ):
                return Response(
                    {"detail": "Autenticação profissional obrigatória."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        log_access(
            request,
            AuditLog.Action.VIEW,
            room.appointment,
            f"Acesso de telemedicina: {role}",
        )
        return Response(
            {
                "appointment_start": room.appointment.start_time,
                "appointment_end": room.appointment.end_time,
                "patient_name": room.appointment.patient.display_name,
                "therapist_name": room.appointment.therapist.full_name,
                "status": room.status,
                "role": role,
                "expires_at": room.expires_at,
            }
        )
