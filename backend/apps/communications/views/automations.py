from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog

from ..models import CommunicationAutomation, CommunicationChannelConfig
from ..permissions import CanAccessCommunications, CanManageCommunicationAutomations
from ..serializers import CommunicationAutomationRunSerializer, CommunicationAutomationSerializer
from ..services import enforce_automation_creation
from .common import _audit


class CommunicationAutomationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanAccessCommunications, CanManageCommunicationAutomations]
    serializer_class = CommunicationAutomationSerializer

    def get_queryset(self):
        return CommunicationAutomation.objects.filter(owner=self.request.user).select_related("template").prefetch_related("runs")

    def perform_create(self, serializer):
        enforce_automation_creation(self.request.user)
        serializer.save()
        _audit(self.request, AuditLog.Action.CREATE, serializer.instance, "communication_automation_created")

    def perform_update(self, serializer):
        serializer.save()
        _audit(self.request, AuditLog.Action.UPDATE, serializer.instance, "communication_automation_updated")

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        automation = self.get_object()
        channel = CommunicationChannelConfig.objects.filter(owner=request.user, channel=automation.channel, is_active=True, connection_status=CommunicationChannelConfig.ConnectionStatus.CONFIGURED).first()
        if channel is None:
            raise ValidationError("Configure e ative o canal antes de habilitar esta automação.")
        automation.is_active = True
        automation.save(update_fields=["is_active", "updated_at"])
        _audit(request, AuditLog.Action.UPDATE, automation, "communication_automation_activated")
        return Response(self.get_serializer(automation).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        automation = self.get_object()
        automation.is_active = False
        automation.save(update_fields=["is_active", "updated_at"])
        _audit(request, AuditLog.Action.UPDATE, automation, "communication_automation_deactivated")
        return Response(self.get_serializer(automation).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        enforce_automation_creation(request.user)
        source = self.get_object()
        source.pk = None
        source.name = f"{source.name} (cópia)"
        source.is_active = False
        source.created_by = request.user
        source.updated_by = request.user
        source.save()
        return Response(self.get_serializer(source).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="dry-run")
    def dry_run(self, request, pk=None):
        automation = self.get_object()
        return Response({"would_send": bool(automation.template.is_active and not automation.template.is_archived), "event_type": automation.event_type, "channel": automation.channel, "template": automation.template.name, "message": "Teste concluído sem criar ou enviar comunicação."})

    @action(detail=True, methods=["get"])
    def runs(self, request, pk=None):
        automation = self.get_object()
        return Response(CommunicationAutomationRunSerializer(automation.runs.all()[:100], many=True).data)
