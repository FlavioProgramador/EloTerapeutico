from __future__ import annotations

from django.utils import timezone

from apps.communications.models import Communication

from .base import CommunicationProvider, ProviderResult


class InAppProvider(CommunicationProvider):
    channel = Communication.Channel.IN_APP
    name = "in_app"

    def validate_configuration(self, owner=None) -> None:
        return None

    def send(self, communication, recipient) -> ProviderResult:
        from apps.communications.services.notifications import create_notification

        create_notification(
            owner=communication.owner,
            recipient=communication.owner,
            communication=communication,
            title=communication.subject or "Nova notificação",
            message=(communication.body or "")[:500],
            event_type=communication.source_event or communication.category,
            priority=communication.priority,
            internal_url=str(communication.metadata.get("internal_url", ""))[:500],
            action_label="Abrir",
            deduplication_key=f"communication:{communication.pk}",
        )
        return ProviderResult(success=True, status=Communication.Status.DELIVERED)

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        from apps.communications.services.notifications import create_notification

        create_notification(
            owner=owner,
            recipient=owner,
            title="Teste do canal interno",
            message="A central de notificações do Elo Terapêutico está funcionando.",
            event_type="communications.channel_test",
            category="communications",
            deduplication_key=f"channel-test:{owner.pk}:{timezone.now():%Y%m%d%H%M}",
        )
        return ProviderResult(success=True, status=Communication.Status.DELIVERED)
