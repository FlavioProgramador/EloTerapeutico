"""Endpoints de templates de evoluções clínicas."""

from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.audit import AuditLog, log_access

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
            Q(owner=request.user) | Q(owner__isnull=True)
        ).select_related("owner")
        if request.query_params.get("include_inactive") != "true":
            queryset = queryset.filter(is_active=True, archived_at__isnull=True)
        status_filter = request.query_params.get("status")
        if status_filter == "active":
            queryset = queryset.filter(is_active=True, archived_at__isnull=True)
        elif status_filter == "inactive":
            queryset = queryset.filter(is_active=False, archived_at__isnull=True)
        elif status_filter == "archived":
            queryset = queryset.filter(archived_at__isnull=False)
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
                | Q(specialty__icontains=search)
            )
        category = request.query_params.get("category", "").strip()
        specialty = request.query_params.get("specialty", "").strip()
        if category:
            queryset = queryset.filter(category=category)
        if specialty:
            queryset = queryset.filter(specialty=specialty)
        serializer = ClinicalEvolutionTemplateSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        self._ensure_clinical_user(request)
        serializer = ClinicalEvolutionTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wants_system = bool(request.data.get("is_system"))
        if wants_system and not request.user.has_perm("records.manage_system_clinical_templates"):
            self.permission_denied(
                request,
                message="Você não pode criar templates globais.",
            )
        try:
            template = serializer.save(owner=None if wants_system else request.user)
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
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk, *, write=False):
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
        if (
            write
            and template.owner_id is None
            and not request.user.has_perm("records.manage_system_clinical_templates")
        ):
            self.permission_denied(request, message="Template global protegido.")
        return template

    def get(self, request, pk):
        template = self.get_object(request, pk)
        return Response(ClinicalEvolutionTemplateSerializer(template).data)

    def patch(self, request, pk):
        template = self.get_object(request, pk, write=True)
        serializer = ClinicalEvolutionTemplateSerializer(
            template,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        try:
            template = serializer.save()
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
        template = self.get_object(request, pk, write=True)
        template.is_active = False
        template.archived_at = timezone.now()
        template.save(update_fields=["is_active", "archived_at", "updated_at"])
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template clínico #{template.id} arquivado",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @transaction.atomic
    def post(self, request, pk):
        action = request.data.get("action")
        template = self.get_object(request, pk, write=action != "duplicate")
        if action == "duplicate":
            base_name = f"Cópia de {template.name}"
            name = base_name
            suffix = 2
            while ClinicalEvolutionTemplate.objects.filter(
                owner=request.user,
                name=name,
            ).exists():
                name = f"{base_name} ({suffix})"
                suffix += 1
            copy = ClinicalEvolutionTemplate.objects.create(
                owner=request.user,
                name=name,
                description=template.description,
                category=template.category,
                specialty=template.specialty,
                content=template.content,
                is_active=True,
                sort_order=template.sort_order,
            )
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
        if action == "activate":
            template.is_active = True
            template.archived_at = None
        elif action == "deactivate":
            template.is_active = False
            template.archived_at = None
        elif action == "archive":
            template.is_active = False
            template.archived_at = timezone.now()
        elif action == "mark_used":
            ClinicalEvolutionTemplate.objects.filter(pk=template.pk).update(usage_count=F("usage_count") + 1)
            template.refresh_from_db()
        else:
            return Response(
                {"detail": "Ação inválida."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if action != "mark_used":
            template.save(update_fields=["is_active", "archived_at", "updated_at"])
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Ação {action} aplicada ao template clínico #{template.id}",
        )
        return Response(ClinicalEvolutionTemplateSerializer(template).data)
