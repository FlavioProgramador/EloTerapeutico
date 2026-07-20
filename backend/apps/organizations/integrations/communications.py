"""Integração de convites com a fila persistente de Comunicações."""

from __future__ import annotations

from django.conf import settings


def enqueue_invitation_email(*, invitation, raw_token: str) -> None:
    from apps.communications.services.system import create_system_email

    base_url = settings.FRONTEND_URL.rstrip("/")
    acceptance_url = f"{base_url}/convites/aceitar/{raw_token}"
    create_system_email(
        owner=invitation.invited_by,
        created_by=invitation.invited_by,
        destination=invitation.email,
        subject=f"Convite para {invitation.organization.name}",
        body=(
            f"Você foi convidado para participar de {invitation.organization.name}. "
            f"Acesse {acceptance_url} para aceitar o convite. "
            "O link é individual, temporário e não deve ser compartilhado."
        ),
        idempotency_key=f"organization-invitation:{invitation.pk}:{invitation.updated_at.timestamp()}",
        source_object_type="organization_invitation",
        source_object_id=str(invitation.pk),
    )
