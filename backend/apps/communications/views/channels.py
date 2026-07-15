from __future__ import annotations

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..channel_serializers import CommunicationChannelConfigSerializer
from ..models import Communication, CommunicationChannelConfig
from ..permissions import CanAccessCommunications, CanManageCommunicationChannels
from ..providers import ProviderError, get_provider
from ..services import ensure_default_channels
from ..services.channels import (
    get_channel_catalog,
    remove_channel_configuration,
    validate_channel_configuration,
)
from .common import _rate_limit


class CommunicationChannelViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, CanAccessCommunications, CanManageCommunicationChannels]
    serializer_class = CommunicationChannelConfigSerializer
    lookup_field = "channel"

    def get_queryset(self):
        ensure_default_channels(self.request.user)
        return CommunicationChannelConfig.objects.filter(owner=self.request.user).order_by("channel")

    @action(detail=False, methods=["get"])
    def catalog(self, request):
        return Response(get_channel_catalog())

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request, channel=None):
        _rate_limit(f"channel-connection-test:{request.user.pk}:{channel}", limit=5, window_seconds=300)
        config = validate_channel_configuration(self.get_object())
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, channel=None):
        config = self.get_object()
        if config.connection_status != CommunicationChannelConfig.ConnectionStatus.CONFIGURED:
            raise ValidationError("Teste a configuração com sucesso antes de ativar o canal.")
        config.is_active = True
        config.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, channel=None):
        config = self.get_object()
        config.is_active = False
        config.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def test(self, request, channel=None):
        _rate_limit(f"channel-message-test:{request.user.pk}:{channel}", limit=3, window_seconds=300)
        config = validate_channel_configuration(self.get_object())
        destination = str(request.data.get("destination") or "").strip()
        if not destination:
            if config.channel == Communication.Channel.EMAIL:
                destination = request.user.email
            elif config.channel in {
                Communication.Channel.WHATSAPP_MANUAL,
                Communication.Channel.WHATSAPP,
                Communication.Channel.SMS,
            }:
                destination = request.user.phone or ""

        provider = get_provider(config.channel, config=config)
        try:
            result = provider.send_test(request.user, destination or None)
        except ProviderError as exc:
            config.connection_status = CommunicationChannelConfig.ConnectionStatus.ERROR
            config.last_tested_at = timezone.now()
            config.last_error_code = exc.__class__.__name__[:80]
            config.last_error_message = str(exc)[:255] or "Falha ao enviar a mensagem de teste."
            config.save(
                update_fields=[
                    "connection_status",
                    "last_tested_at",
                    "last_error_code",
                    "last_error_message",
                    "updated_at",
                ]
            )
            raise ValidationError(config.last_error_message) from exc

        safe_metadata = {
            key: value
            for key, value in result.metadata.items()
            if key in {"manual_url", "requires_confirmation", "provider_status", "price", "price_unit"}
        }
        return Response(
            {
                "channel": self.get_serializer(config).data,
                "test": {
                    "success": result.success,
                    "status": result.status,
                    "external_id": result.provider_message_id,
                    "metadata": safe_metadata,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"])
    def remove(self, request, channel=None):
        _rate_limit(f"channel-remove:{request.user.pk}:{channel}", limit=5, window_seconds=300)
        if request.data.get("confirm") is not True:
            raise ValidationError({"confirm": "Confirme a remoção da configuração."})
        config = remove_channel_configuration(self.get_object())
        return Response(self.get_serializer(config).data)
