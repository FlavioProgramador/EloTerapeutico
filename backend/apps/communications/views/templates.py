import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.organizations.models import OrganizationMembership
from apps.organizations.services.tenant_context import ensure_request_organization

from ..models import CommunicationTemplate
from ..permissions import CanAccessCommunications, CanManageCommunicationTemplates
from ..selectors import templates_for_user
from ..serializers import CommunicationTemplateSerializer
from ..services import enforce_template_creation
from ..validators import plain_text_to_safe_html, render_template_text, validate_template_text
from .common import _audit, _rate_limit


class CommunicationTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
        CanAccessCommunications,
        CanManageCommunicationTemplates,
    ]
    serializer_class = CommunicationTemplateSerializer

    def _context(self):
        return ensure_request_organization(request=self.request, required=True)

    def get_queryset(self):
        organization, _ = self._context()
        queryset = templates_for_user(
            self.request.user,
            organization=organization,
        )
        if self.request.query_params.get("channel"):
            queryset = queryset.filter(channel=self.request.query_params["channel"])
        if self.request.query_params.get("search"):
            query = self.request.query_params["search"].strip()
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset

    def _ensure_editable(self, template):
        _, membership = self._context()
        if template.is_system_template:
            raise ValidationError("Template do sistema não pode ser alterado.")
        if membership.role == OrganizationMembership.Role.THERAPIST and (
            template.owner_id != self.request.user.pk
        ):
            raise ValidationError("Template pertence a outro profissional.")

    def perform_create(self, serializer):
        enforce_template_creation(self.request.user)
        serializer.save()
        _audit(
            self.request,
            AuditLog.Action.CREATE,
            serializer.instance,
            "communication_template_created",
        )

    def perform_update(self, serializer):
        self._ensure_editable(serializer.instance)
        serializer.save()
        _audit(
            self.request,
            AuditLog.Action.UPDATE,
            serializer.instance,
            "communication_template_updated",
        )

    def perform_destroy(self, instance):
        self._ensure_editable(instance)
        instance.is_archived = True
        instance.save(update_fields=["is_archived", "updated_at"])

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        organization, _ = self._context()
        enforce_template_creation(request.user)
        source = self.get_object()
        copy = CommunicationTemplate.objects.create(
            organization=organization,
            owner=request.user,
            name=f"{source.name} (cópia)",
            slug=f"{source.slug}-{uuid.uuid4().hex[:8]}",
            description=source.description,
            category=source.category,
            channel=source.channel,
            subject_template=source.subject_template,
            body_template=source.body_template,
            allowed_variables=source.allowed_variables,
            is_system_template=False,
            created_by=request.user,
            updated_by=request.user,
        )
        return Response(
            self.get_serializer(copy).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        template = self.get_object()
        self._ensure_editable(template)
        template.is_archived = True
        template.save(update_fields=["is_archived", "updated_at"])
        return Response(self.get_serializer(template).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        organization, membership = self._context()
        template = CommunicationTemplate.objects.filter(
            pk=pk,
            organization=organization,
            is_system_template=False,
        ).first()
        if template is None:
            raise ValidationError("Template não encontrado.")
        if membership.role == OrganizationMembership.Role.THERAPIST and (
            template.owner_id != request.user.pk
        ):
            raise ValidationError("Template pertence a outro profissional.")
        template.is_archived = False
        template.save(update_fields=["is_archived", "updated_at"])
        return Response(self.get_serializer(template).data)

    @action(detail=False, methods=["post"])
    def preview(self, request):
        organization, _ = self._context()
        _rate_limit(
            f"preview:{organization.pk}:{request.user.pk}",
            limit=60,
            window_seconds=60,
        )
        subject_template = str(request.data.get("subject_template", ""))
        body_template = str(request.data.get("body_template", ""))
        variables = request.data.get("variables") or {}
        allowed = validate_template_text(subject_template, body_template)
        demo = {key: f"[Exemplo: {key}]" for key in allowed}
        demo.update(
            {key: str(value) for key, value in variables.items() if key in allowed}
        )
        try:
            subject = render_template_text(subject_template, demo)
            body = render_template_text(body_template, demo)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(
            {
                "subject": subject,
                "body": body,
                "body_html": plain_text_to_safe_html(body),
            }
        )
