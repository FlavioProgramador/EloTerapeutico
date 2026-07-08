# mypy: ignore-errors
import hashlib
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import AuditLog, log_access

from ..models import PatientRegistrationInvite


class PatientInviteActions:
    @action(detail=True, methods=["post"], url_path="registration-link")
    def registration_link(self, request, pk=None):
        patient = self.get_object()
        if request.user.is_secretary:
            return Response(
                {"detail": "Seu perfil não pode gerar links de cadastro."},
                status=status.HTTP_403_FORBIDDEN,
            )

        PatientRegistrationInvite.objects.filter(
            patient=patient,
            used_at__isnull=True,
        ).update(used_at=timezone.now())
        public_value = f"{uuid4().hex}{uuid4().hex}"
        invite = PatientRegistrationInvite.objects.create(
            patient=patient,
            token_hash=hashlib.sha256(public_value.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=72),
            created_by=request.user,
        )
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=patient,
            obj_repr=f"Convite cadastral do paciente #{patient.pk}",
        )
        return Response(
            {
                "path": f"/cadastro-paciente/{public_value}",
                "expires_at": invite.expires_at,
            },
            status=status.HTTP_201_CREATED,
        )
