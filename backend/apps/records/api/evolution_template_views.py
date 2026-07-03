"""Endpoints de templates de evoluções clínicas."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditLog, log_access

from ..evolution_flow_models import ClinicalEvolutionTemplate
from .evolution_serializers import ClinicalEvolutionTemplateSerializer


class ClinicalEvolutionTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def _ensure_clinical_user(self, request):
        if request.user.is_secretary:
            self.permission_denied(
                request,
                message="Secretárias não acessam templates clínicos.",
            )

    def get(self, request):
        self._ensure_clinical_user(request)
        queryset = ClinicalEvolutionTemplate.objects.filter(
            Q(owner=request.user) | Q(owner__isnull=True),
            is_active=True,
        ).select_related("owner")
        serializer = ClinicalEvolutionTemplateSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        self._ensure_clinical_user(request)
        serializer = ClinicalEvolutionTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wants_system = bool(request.data.get("is_system"))
        if wants_system and not request.user.has_perm(
            "records.manage_system_clinical_templates"
        ):
            self.permission_denied(
                request,
                message="Você não pode criar templates globais.",
            )
        template = serializer.save(owner=None if wants_system else request.user)
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
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        template = get_object_or_404(
            ClinicalEvolutionTemplate.objects.select_related("owner"),
            pk=pk,
        )
        if request.user.is_secretary:
            self.permission_denied(
                request,
                message="Acesso clínico não permitido.",
            )
        if template.owner_id not in (None, request.user.id):
            self.permission_denied(request, message="Template não autorizado.")
        if template.owner_id is None and not request.user.has_perm(
            "records.manage_system_clinical_templates"
        ):
            self.permission_denied(request, message="Template global protegido.")
        return template

    def patch(self, request, pk):
        template = self.get_object(request, pk)
        serializer = ClinicalEvolutionTemplateSerializer(
            template,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} atualizado",
        )
        return Response(ClinicalEvolutionTemplateSerializer(template).data)

    def delete(self, request, pk):
        template = self.get_object(request, pk)
        template.is_active = False
        template.save(update_fields=["is_active", "updated_at"])
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} desativado",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
