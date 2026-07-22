from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.communications.services import CommunicationBlocked
from apps.scheduling.api.v1.serializers import (
    AppointmentReminderSerializer,
    TelemedicineConsentSerializer,
    TelemedicineInvitationSendSerializer,
    TelemedicineInvitationTokenSerializer,
    TelemedicineParticipantRemovalSerializer,
    TelemedicinePublicLeaveSerializer,
    TelemedicineRoomSerializer,
)
from apps.scheduling.exceptions import (
    TelemedicineAccessDeniedError,
    TelemedicineConsentRequiredError,
    TelemedicineDisabledError,
    TelemedicineEncryptionUnavailableError,
    TelemedicineInvalidStateError,
    TelemedicineInvitationExpiredError,
    TelemedicineOutsideJoinWindowError,
    TelemedicineProviderUnavailableError,
    TelemedicineUnavailableError,
)
from apps.scheduling.integrations.communications import (
    send_telemedicine_invitation,
)
from apps.scheduling.integrations.telemedicine import (
    TelemedicineWebhookVerificationError,
)
from apps.scheduling.selectors.resources import (
    appointment_reminders_queryset,
    telemedicine_rooms_queryset,
)
from apps.scheduling.services.telemedicine import (
    cancel_appointment_reminder,
    create_patient_invitation,
    exchange_patient_invitation,
    finish_telemedicine_room,
    issue_patient_join_credentials,
    issue_professional_join_credentials,
    process_telemedicine_webhook,
    record_telemedicine_consent,
    remove_telemedicine_participant,
    revoke_patient_invitation,
)
from apps.scheduling.services.telemedicine_public import (
    leave_patient_telemedicine,
)
from apps.scheduling.services.telemedicine_rooms import (
    validate_professional_access,
)

from .base import ScopedAgendaMixin


def _no_store(response: Response) -> Response:
    response["Cache-Control"] = "no-store, private, max-age=0"
    response["Pragma"] = "no-cache"
    response["Referrer-Policy"] = "no-referrer"
    return response


def _telemedicine_error_response(exc: Exception) -> Response:
    if isinstance(exc, TelemedicineInvitationExpiredError):
        code = status.HTTP_410_GONE
    elif isinstance(exc, TelemedicineConsentRequiredError):
        code = status.HTTP_428_PRECONDITION_REQUIRED
    elif isinstance(exc, TelemedicineOutsideJoinWindowError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, TelemedicineAccessDeniedError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(
        exc,
        (
            TelemedicineDisabledError,
            TelemedicineProviderUnavailableError,
            TelemedicineEncryptionUnavailableError,
        ),
    ):
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, TelemedicineInvalidStateError):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_410_GONE
    return _no_store(Response({"detail": str(exc)}, status=code))


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

    def _create_invitation_response(self, request, room):
        try:
            validate_professional_access(actor=request.user, room=room)
            invitation, _raw_token, invitation_url = create_patient_invitation(
                actor=request.user,
                room=room,
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Convite de telemedicina regenerado",
        )
        return _no_store(
            Response(
                {
                    "invitation_url": invitation_url,
                    "expires_at": invitation.expires_at,
                },
                status=status.HTTP_201_CREATED,
            )
        )

    @action(detail=True, methods=["post"], url_path="create-invitation")
    def create_invitation(self, request, pk=None):
        return self._create_invitation_response(request, self.get_object())

    @action(detail=True, methods=["post"], url_path="regenerate-link")
    def regenerate_link(self, request, pk=None):
        return self._create_invitation_response(request, self.get_object())

    @action(detail=True, methods=["post"], url_path="send-invitation")
    def send_invitation(self, request, pk=None):
        serializer = TelemedicineInvitationSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = self.get_object()
        try:
            communication = send_telemedicine_invitation(
                actor=request.user,
                room=room,
                channel=serializer.validated_data["channel"],
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        except (CommunicationBlocked, PermissionDenied, ValidationError) as exc:
            detail = getattr(exc, "message", None) or str(exc)
            return Response(
                {"detail": detail},
                status=status.HTTP_409_CONFLICT,
            )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Convite de telemedicina enfileirado para envio",
        )
        return Response(
            {
                "communication_id": communication.pk,
                "status": communication.status,
                "channel": communication.channel,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="revoke-invitation")
    def revoke_invitation(self, request, pk=None):
        room = self.get_object()
        try:
            validate_professional_access(actor=request.user, room=room)
            invitation = revoke_patient_invitation(
                actor=request.user,
                room=room,
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Convite de telemedicina revogado",
        )
        return Response(
            {"revoked": bool(invitation)},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="join-professional")
    def join_professional(self, request, pk=None):
        room = self.get_object()
        try:
            credentials = issue_professional_join_credentials(
                actor=request.user,
                room=room,
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        log_access(
            request,
            AuditLog.Action.VIEW,
            room.appointment,
            "Profissional autorizado para sala de telemedicina",
        )
        return _no_store(Response(credentials))

    @action(detail=True, methods=["post"], url_path="open-room")
    def open_room(self, request, pk=None):
        return self.join_professional(request, pk=pk)

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        room = self.get_object()
        try:
            room = finish_telemedicine_room(
                actor=request.user,
                room=room,
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Sala de telemedicina encerrada",
        )
        return Response(self.get_serializer(room).data)

    @action(detail=True, methods=["post"], url_path="remove-participant")
    def remove_participant(self, request, pk=None):
        serializer = TelemedicineParticipantRemovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = self.get_object()
        try:
            remove_telemedicine_participant(
                actor=request.user,
                room=room,
                identity=serializer.validated_data["identity"],
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            room.appointment,
            "Participante removido da sala de telemedicina",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="status")
    def room_status(self, request, pk=None):
        return Response(self.get_serializer(self.get_object()).data)


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


@method_decorator(
    ratelimit(key="ip", rate="20/m", block=True, method="POST"),
    name="post",
)
class TelemedicinePublicExchangeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TelemedicineInvitationTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            context = exchange_patient_invitation(
                raw_token=serializer.validated_data["token"]
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        return _no_store(Response(context))


@method_decorator(
    ratelimit(key="ip", rate="10/m", block=True, method="POST"),
    name="post",
)
class TelemedicinePublicConsentView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TelemedicineConsentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            consent = record_telemedicine_consent(
                raw_token=serializer.validated_data["token"],
                accepted=serializer.validated_data["accepted"],
                responsible_guardian_name=serializer.validated_data.get(
                    "responsible_guardian_name", ""
                ),
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        return _no_store(
            Response(
                {
                    "accepted": True,
                    "document_version": consent.document_version,
                    "accepted_at": consent.accepted_at,
                }
            )
        )


@method_decorator(
    ratelimit(key="ip", rate="10/m", block=True, method="POST"),
    name="post",
)
class TelemedicinePublicJoinView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TelemedicineInvitationTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            credentials = issue_patient_join_credentials(
                raw_token=serializer.validated_data["token"]
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        return _no_store(Response(credentials))


@method_decorator(
    ratelimit(key="ip", rate="20/m", block=True, method="POST"),
    name="post",
)
class TelemedicinePublicLeaveView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TelemedicinePublicLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            leave_patient_telemedicine(
                raw_token=serializer.validated_data["token"],
                identity=serializer.validated_data["identity"],
            )
        except TelemedicineUnavailableError as exc:
            return _telemedicine_error_response(exc)
        return _no_store(Response(status=status.HTTP_204_NO_CONTENT))


class LiveKitWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw_body = request.body.decode("utf-8")
        authorization = request.headers.get("Authorization", "")
        try:
            event, processed = process_telemedicine_webhook(
                raw_body=raw_body,
                authorization=authorization,
            )
        except TelemedicineWebhookVerificationError:
            return Response(
                {"detail": "Webhook inválido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {"accepted": True, "processed": processed, "event_id": event.pk},
            status=status.HTTP_200_OK,
        )


class TelemedicineAccessView(APIView):
    """Endpoint legado mantido temporariamente sem conceder acesso."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, role, token):
        del request, role, token
        return _no_store(
            Response(
                {"detail": "Este link foi substituído por um convite mais seguro."},
                status=status.HTTP_410_GONE,
            )
        )
