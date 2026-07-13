import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog

from ..models import CommunicationTemplate
from ..permissions import CanAccessCommunications, CanManageCommunicationTemplates
from ..selectors import templates_for_user
from ..serializers import CommunicationTemplateSerializer
from ..services import enforce_template_creation
from ..validators import plain_text_to_safe_html, render_template_text, validate_template_text
from .common import _audit, _rate_limit


class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanAccessCommunications, CanManageCommunicationTemplates]
    serializer_class = CommunicationTemplateSerializer

    def get_queryset(self):
        queryset = templates_for_user(self.request.user)
        if self.request.query_params.get("channel"):
            queryset = queryset.filter(channel=self.request.query_params["channel"])
        if self.request.query_params.get("search"):
            query = self.request.query_params["search"].strip()
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        return queryset

    def perform_create(self, serializer):
        enforce_template_creation(self.request.user)
        serializer.save()
        _audit(self.request, AuditLog.Action.CREATE, serializer.instance, "communication_template_created")

    def perform_update(self, serializer):
        serializer.save()
        _audit(self.request, AuditLog.Action.UPDATE, serializer.instance, "communication_template_updated")

    def perform_destroy(self, instance):
        if instance.is_system_template or instance.owner_id != self.request.user.pk:
            raise ValidationError("Este template não pode ser excluído.")
        instance.is_archived = True
        instance.save(update_fields=["is_archived", "updated_at"])

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        enforce_template_creation(request.user)
        source = self.get_object()
        copy = CommunicationTemplate.objects.create(
            owner=request.user,
            name=f"{source.name} (cópia)",
            slug=f"{source.slug}-{uuid.uuid4().hex[:8]}",
            description=source.description,
            category=source.category,
            channel=source.channel,
            subject_template=source.subject_template,
            body_template=source.body_template,
            allowed_variables=source.allowed_variables,
            created_by=request.user,
            updated_by=request.user,
        )
        return Response(self.get_serializer(copy).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        template = self.get_object()
        if template.owner_id != request.user.pk:
            raise ValidationError("Template do sistema não pode ser arquivado.")
        template.is_archived = True
        template.save(update_fields=["is_archived", "updated_at"])
        return Response(self.get_serializer(template).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        template = get_object_or_404(CommunicationTemplate, pk=pk, owner=request.user)
        template.is_archived = False
        template.save(update_fields=["is_archived", "updated_at"])
        return Response(self.get_serializer(template).data)

    @action(detail=False, methods=["post"])
    def preview(self, request):
        _rate_limit(f"preview:{request.user.pk}", limit=60, window_seconds=60)
        subject_template = str(request.data.get("subject_template", ""))
        body_template = str(request.data.get("body_template", ""))
        variables = request.data.get("variables") or {}
        allowed = validate_template_text(subject_template, body_template)
        demo = {key: f"[Exemplo: {key}]" for key in allowed}
        demo.update({key: str(value) for key, value in variables.items() if key in allowed})
        try:
            subject = render_template_text(subject_template, demo)
            body = render_template_text(body_template, demo)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response({"subject": subject, "body": body, "body_html": plain_text_to_safe_html(body)})
