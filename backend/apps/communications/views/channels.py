import uuid

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Communication, CommunicationChannelConfig
from ..permissions import CanAccessCommunications, CanManageCommunicationChannels
from ..serializers import CommunicationChannelConfigSerializer, CommunicationDetailSerializer
from ..services import create_communication, ensure_default_channels
from .common import _rate_limit


class CommunicationChannelViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, CanAccessCommunications, CanManageCommunicationChannels]
    serializer_class = CommunicationChannelConfigSerializer
    lookup_field = "channel"

    def get_queryset(self):
        ensure_default_channels(self.request.user)
        return CommunicationChannelConfig.objects.filter(owner=self.request.user).order_by("channel")

    @action(detail=True, methods=["post"])
    def activate(self, request, channel=None):
        config = self.get_object()
        if config.connection_status == CommunicationChannelConfig.ConnectionStatus.DISABLED and config.channel in {Communication.Channel.IN_APP, Communication.Channel.EMAIL, Communication.Channel.WHATSAPP_MANUAL}:
            config.connection_status = CommunicationChannelConfig.ConnectionStatus.CONFIGURED
        if config.connection_status != CommunicationChannelConfig.ConnectionStatus.CONFIGURED:
            raise ValidationError("O canal não está configurado.")
        config.is_active = True
        config.save(update_fields=["is_active", "connection_status", "updated_at"])
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, channel=None):
        config = self.get_object()
        config.is_active = False
        config.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(config).data)

    @action(detail=True, methods=["post"])
    def test(self, request, channel=None):
        _rate_limit(f"channel-test:{request.user.pk}:{channel}", limit=3, window_seconds=300)
        config = self.get_object()
        if not config.is_active or config.connection_status != CommunicationChannelConfig.ConnectionStatus.CONFIGURED:
            raise ValidationError("O canal não está configurado e ativo.")
        controlled_destination = request.user.email if config.channel == Communication.Channel.EMAIL else None
        if config.channel in {Communication.Channel.WHATSAPP_MANUAL, Communication.Channel.WHATSAPP, Communication.Channel.SMS}:
            if not request.user.phone:
                raise ValidationError("Cadastre seu telefone antes de testar este canal.")
            controlled_destination = request.user.phone
        communication = create_communication(
            owner=request.user,
            created_by=request.user,
            channel=config.channel,
            category=Communication.Category.SYSTEM_NOTIFICATION,
            subject="Teste do canal de comunicação",
            body="Este é um teste controlado do canal de comunicação do Elo Terapêutico.",
            idempotency_key=f"channel-test:{request.user.pk}:{channel}:{uuid.uuid4().hex}",
            source_event="channel.test",
            controlled_destination=controlled_destination,
        )
        return Response(CommunicationDetailSerializer(communication).data, status=status.HTTP_202_ACCEPTED)
