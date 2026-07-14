"""Endpoints de templates de evoluções clínicas."""

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.records.exceptions import InvalidClinicalTemplateAction
from apps.records.permissions import CanAccessClinicalTemplates, can_access_clinical_template
from apps.records.selectors import clinical_templates_for_user
from apps.records.services import (
    apply_clinical_template_action,
    archive_clinical_template,
    create_clinical_template,
    duplicate_clinical_template,
    update_clinical_template,
)

from .evolution_serializers import ClinicalEvolutionTemplateSerializer


class ClinicalEvolutionTemplateListCreateView(APIView):
    permission_classes = [CanAccessClinicalTemplates]

    def get(self, request):
        queryset = clinical_templates_for_user(user=request.user, params=request.query_params)
        return Response(ClinicalEvolutionTemplateSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = ClinicalEvolutionTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wants_system = bool(request.data.get("is_system"))
        if wants_system and not request.user.has_perm("records.manage_system_clinical_templates"):
            self.permission_denied(request, message="Você não pode criar templates globais.")
        try:
            template = create_clinical_template(
                actor=request.user,
                validated_data=dict(serializer.validated_data),
                is_system=wants_system,
            )
        except IntegrityError:
            return Response(
                {"name": ["Já existe um template com este nome neste escopo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} criado",
        )
        return Response(
            ClinicalEvolutionTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED,
        )


class ClinicalEvolutionTemplateDetailView(APIView):
    permission_classes = [CanAccessClinicalTemplates]

    def get_object(self, request, pk, *, write=False):
        template = get_object_or_404(
            clinical_templates_for_user(
                user=request.user,
                params={"include_inactive": "true"},
            ),
            pk=pk,
        )
        if not can_access_clinical_template(
            user=request.user,
            template=template,
            write=write,
        ):
            self.permission_denied(
                request,
                message="Template global protegido." if template.owner_id is None else "Template não autorizado.",
            )
        return template

    def get(self, request, pk):
        return Response(ClinicalEvolutionTemplateSerializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        template = self.get_object(request, pk, write=True)
        serializer = ClinicalEvolutionTemplateSerializer(template, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            template = update_clinical_template(
                template=template,
                validated_data=dict(serializer.validated_data),
            )
        except IntegrityError:
            return Response(
                {"name": ["Já existe um template com este nome neste escopo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} atualizado",
        )
        return Response(ClinicalEvolutionTemplateSerializer(template).data)

    def delete(self, request, pk):
        template = archive_clinical_template(template=self.get_object(request, pk, write=True))
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} arquivado",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, pk):
        action = request.data.get("action")
        template = self.get_object(request, pk, write=action != "duplicate")
        if action == "duplicate":
            copy = duplicate_clinical_template(actor=request.user, template=template)
            log_access(
                request,
                AuditLog.Action.CREATE,
                obj=copy,
                obj_repr=f"Template clínico #{template.id} duplicado como #{copy.id}",
            )
            return Response(
                ClinicalEvolutionTemplateSerializer(copy).data,
                status=status.HTTP_201_CREATED,
            )
        try:
            template = apply_clinical_template_action(template=template, action=action)
        except InvalidClinicalTemplateAction as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Ação {action} aplicada ao template clínico #{template.id}",
        )
        return Response(ClinicalEvolutionTemplateSerializer(template).data)
