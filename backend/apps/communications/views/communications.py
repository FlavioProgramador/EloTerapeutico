from __future__ import annotations

import uuid
from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog

from ..models import Communication
from ..permissions import CanAccessCommunications, CanSendCommunication
from ..selectors import communications_for_user
from ..serializers import (
    CommunicationCreateSerializer,
    CommunicationDetailSerializer,
    CommunicationDraftUpdateSerializer,
    CommunicationListSerializer,
)
from ..services import (
    cancel_communication,
    create_communication,
    mark_manual_opened,
    mark_manually_sent,
    retry_communication,
)
from .common import _audit, _rate_limit


class CommunicationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, CanAccessCommunications, CanSendCommunication]
    lookup_field = "public_id"

    def get_queryset(self):
        queryset = communications_for_user(self.request.user)
        params = self.request.query_params
        if params.get("search"):
            search = params["search"].strip()
            queryset = queryset.filter(Q(subject__icontains=search) | Q(patient__full_name__icontains=search) | Q(source_event__icontains=search))
        for field in ("channel", "category", "status"):
            if params.get(field):
                queryset = queryset.filter(**{field: params[field]})
        if params.get("patient"):
            queryset = queryset.filter(patient_id=params["patient"])
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return CommunicationCreateSerializer
        if self.action == "retrieve":
            return CommunicationDetailSerializer
        if self.action in {"update", "partial_update"}:
            return CommunicationDraftUpdateSerializer
        return CommunicationListSerializer

    def create(self, request, *args, **kwargs):
        _rate_limit(f"create:{request.user.pk}", limit=30, window_seconds=60)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        communication = serializer.save()
        _audit(request, AuditLog.Action.CREATE, communication, "communication_created")
        return Response(CommunicationDetailSerializer(communication).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        communication = serializer.save()
        _audit(self.request, AuditLog.Action.UPDATE, communication, "communication_draft_updated")

    def destroy(self, request, *args, **kwargs):
        communication = self.get_object()
        if not communication.is_terminal and communication.status != Communication.Status.FAILED:
            cancel_communication(communication, actor=request.user)
        communication.archived_at = timezone.now()
        communication.save(update_fields=["archived_at", "updated_at"])
        _audit(request, AuditLog.Action.DELETE, communication, "communication_archived")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def send(self, request, public_id=None):
        communication = self.get_object()
        if communication.status != Communication.Status.DRAFT:
            raise ValidationError("Somente rascunhos podem ser enviados por esta ação.")
        if communication.channel == Communication.Channel.WHATSAPP_MANUAL and communication.metadata.get("manual_url"):
            raise ValidationError("Abra o WhatsApp e confirme o envio manual em vez de reenfileirar esta mensagem.")
        communication.status = Communication.Status.QUEUED
        communication.queued_at = timezone.now()
        communication.save(update_fields=["status", "queued_at", "updated_at"])
        _audit(request, AuditLog.Action.UPDATE, communication, "communication_queued")
        return Response(CommunicationDetailSerializer(communication).data)

    @action(detail=True, methods=["post"])
    def schedule(self, request, public_id=None):
        communication = self.get_object()
        if communication.status != Communication.Status.DRAFT:
            raise ValidationError("Somente rascunhos podem ser agendados.")
        value = request.data.get("scheduled_at")
        if not value:
            raise ValidationError({"scheduled_at": "Informe a data do agendamento."})
        try:
            scheduled_at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError({"scheduled_at": "Data inválida."}) from exc
        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at)
        if scheduled_at <= timezone.now():
            raise ValidationError({"scheduled_at": "A data deve estar no futuro."})
        communication.status = Communication.Status.SCHEDULED
        communication.scheduled_at = scheduled_at
        communication.save(update_fields=["status", "scheduled_at", "updated_at"])
        return Response(CommunicationDetailSerializer(communication).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, public_id=None):
        communication = cancel_communication(self.get_object(), actor=request.user)
        _audit(request, AuditLog.Action.UPDATE, communication, "communication_canceled")
        return Response(CommunicationDetailSerializer(communication).data)

    @action(detail=True, methods=["post"])
    def retry(self, request, public_id=None):
        _rate_limit(f"retry:{request.user.pk}", limit=10, window_seconds=60)
        communication = retry_communication(self.get_object())
        _audit(request, AuditLog.Action.UPDATE, communication, "communication_retried")
        return Response(CommunicationDetailSerializer(communication).data)

    @action(detail=True, methods=["post"], url_path="open-manual")
    def open_manual(self, request, public_id=None):
        communication = mark_manual_opened(self.get_object())
        _audit(request, AuditLog.Action.VIEW, communication, "communication_manual_link_opened")
        return Response({"url": communication.metadata.get("manual_url", "")})

    @action(detail=True, methods=["post"], url_path="mark-manually-sent")
    def mark_manually_sent(self, request, public_id=None):
        communication = mark_manually_sent(self.get_object())
        _audit(request, AuditLog.Action.UPDATE, communication, "communication_manually_sent")
        return Response(CommunicationDetailSerializer(communication).data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, public_id=None):
        source = self.get_object()
        duplicate = create_communication(
            owner=request.user,
            created_by=request.user,
            channel=source.channel,
            category=source.category,
            patient=source.patient,
            appointment=source.appointment,
            subject=source.subject,
            body=source.body,
            priority=source.priority,
            idempotency_key=f"duplicate:{source.pk}:{uuid.uuid4().hex}",
            source_event="manual.duplicate",
            draft=True,
        )
        return Response(CommunicationDetailSerializer(duplicate).data, status=status.HTTP_201_CREATED)
