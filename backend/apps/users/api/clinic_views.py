"""API da fundação multi-tenant e da clínica ativa por sessão."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.users.models import AuthSession, ClinicMembership
from apps.users.services.clinics import (
    accept_clinic_invitation,
    active_memberships_for_user,
    create_clinic_invitation,
    membership_can_manage_clinic,
    resolve_active_membership,
    switch_active_clinic,
)
from apps.users.services.sessions import SESSION_CLAIM

from .clinic_serializers import (
    ClinicInvitationAcceptSerializer,
    ClinicInvitationCreateSerializer,
    ClinicInvitationSerializer,
    ClinicMembershipSerializer,
    ClinicSwitchSerializer,
)


def _current_session(request) -> AuthSession | None:
    token = getattr(request, "auth", None)
    try:
        session_id = token.get(SESSION_CLAIM) if token is not None else None
    except AttributeError:
        session_id = None
    if not session_id:
        return None
    return (
        AuthSession.objects.select_related("active_clinic")
        .filter(
            public_id=session_id,
            user=request.user,
            revoked_at__isnull=True,
        )
        .first()
    )


def _serialize_memberships(request, *, active_membership=None):
    memberships = active_memberships_for_user(user=request.user)
    active_clinic_id = active_membership.clinic_id if active_membership else None
    return ClinicMembershipSerializer(
        memberships,
        many=True,
        context={"request": request, "active_clinic_id": active_clinic_id},
    ).data


@extend_schema(tags=["users"])
class ClinicContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = _current_session(request)
        active_membership = resolve_active_membership(
            user=request.user,
            session=session,
            persist_fallback=session is not None,
        )
        return Response(
            {
                "active_membership": (
                    ClinicMembershipSerializer(
                        active_membership,
                        context={
                            "request": request,
                            "active_clinic_id": (
                                active_membership.clinic_id if active_membership else None
                            ),
                        },
                    ).data
                    if active_membership
                    else None
                ),
                "memberships": _serialize_memberships(
                    request,
                    active_membership=active_membership,
                ),
                "requires_setup": (
                    active_membership is None
                    and request.user.role in {request.user.Role.THERAPIST, request.user.Role.ADMIN}
                ),
            }
        )


@extend_schema(tags=["users"], request=ClinicSwitchSerializer)
class ClinicSwitchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClinicSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = _current_session(request)
        if session is None:
            raise AuthenticationFailed("Sessão incompatível com troca de clínica.")

        membership = switch_active_clinic(
            user=request.user,
            session=session,
            clinic_public_id=serializer.validated_data["clinic_id"],
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=membership.clinic,
            obj_repr=f"users.Clinic#{membership.clinic_id}:active_session_switch",
        )
        return Response(
            {
                "message": "Clínica ativa alterada com sucesso.",
                "active_membership": ClinicMembershipSerializer(
                    membership,
                    context={
                        "request": request,
                        "active_clinic_id": membership.clinic_id,
                    },
                ).data,
            }
        )


@extend_schema(tags=["users"], request=ClinicInvitationCreateSerializer)
class ClinicInvitationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClinicInvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = _current_session(request)
        active_membership = resolve_active_membership(
            user=request.user,
            session=session,
            persist_fallback=session is not None,
        )
        if not membership_can_manage_clinic(active_membership):
            raise Http404("Clínica não encontrada.")

        try:
            invitation, raw_token = create_clinic_invitation(
                actor=request.user,
                clinic=active_membership.clinic,
                **serializer.validated_data,
            )
        except DjangoValidationError as exc:
            raise ValidationError({"detail": list(exc.messages)}) from exc

        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=invitation,
            obj_repr=f"users.ClinicInvitation#{invitation.pk}",
        )
        return Response(
            {
                "invitation": ClinicInvitationSerializer(invitation).data,
                "invitation_token": raw_token,
                "displayed_once": True,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["users"], request=ClinicInvitationAcceptSerializer)
class ClinicInvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ClinicInvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            membership = accept_clinic_invitation(
                user=request.user,
                raw_token=serializer.validated_data["token"],
            )
        except DjangoValidationError as exc:
            raise ValidationError({"detail": list(exc.messages)}) from exc

        session = _current_session(request)
        if session is not None and session.active_clinic_id is None:
            membership = switch_active_clinic(
                user=request.user,
                session=session,
                clinic_public_id=membership.clinic.public_id,
            )

        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=membership,
            obj_repr=f"users.ClinicMembership#{membership.pk}:invitation_accepted",
        )
        return Response(
            {
                "message": "Convite aceito com sucesso.",
                "membership": ClinicMembershipSerializer(
                    membership,
                    context={
                        "request": request,
                        "active_clinic_id": session.active_clinic_id if session else None,
                    },
                ).data,
            },
            status=status.HTTP_200_OK,
        )
