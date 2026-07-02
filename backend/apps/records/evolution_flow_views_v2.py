"""Endpoints consolidados do modal de evolução clínica."""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.agenda.models import Appointment
from core.audit import AuditLog, log_access

from .clinical_views import ClinicalPatientMixin, RecordPagination
from .evolution_flow_models import ClinicalEvolutionTemplate
from .evolution_flow_serializers import (
    ClinicalEvolutionTemplateSerializer,
    EvolutionAppointmentOptionSerializer,
    EvolutionAttachmentSerializer,
)
from .evolution_flow_serializers_v2 import EvolutionFlowSerializer
from .evolution_security import can_view_confidential_evolution, max_evolution_attachments
from .extended_models import EvolutionClinicalData
from .models import Evolution
from .treatment_models import ClinicalDocument


class PatientEvolutionFlowView(ClinicalPatientMixin, APIView):
    pagination_class = RecordPagination

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = (
            Evolution.objects.filter(patient=patient)
            .select_related(
                "created_by",
                "clinical_data",
                "appointment",
                "appointment__therapist",
                "appointment__patient",
            )
            .prefetch_related("versions", "documents")
            .order_by("-session_date", "-created_at")
        )
        if not request.user.has_perm("records.view_confidential_evolution"):
            queryset = queryset.filter(Q(is_confidential=False) | Q(created_by=request.user))
        requested_status = request.query_params.get("status")
        if requested_status:
            queryset = queryset.filter(clinical_data__status=requested_status)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = EvolutionFlowSerializer(
            page,
            many=True,
            context={"request": request, "patient": patient},
        )
        return paginator.get_paginated_response(serializer.data)

    @transaction.atomic
    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        if not (request.user.is_therapist or request.user.is_admin_role):
            self.permission_denied(request, message="Seu perfil não pode criar registros clínicos.")
        serializer = EvolutionFlowSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=evolution,
            obj_repr=(
                f"Evolução #{evolution.id} criada; "
                f"confidencial={evolution.is_confidential}"
            ),
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": patient},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EvolutionFlowDetailView(ClinicalPatientMixin, APIView):
    def get(self, request, pk):
        evolution = self.get_evolution(pk)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=evolution,
            obj_repr=f"Visualização da evolução #{evolution.id}",
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": evolution.patient},
            ).data
        )

    @transaction.atomic
    def patch(self, request, pk):
        evolution = self.get_evolution(pk)
        before = evolution.is_confidential
        serializer = EvolutionFlowSerializer(
            evolution,
            data=request.data,
            partial=True,
            context={"request": request, "patient": evolution.patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=(
                f"Evolução #{evolution.id} atualizada; "
                f"confidencialidade_alterada={before != evolution.is_confidential}; "
                f"confidencial={evolution.is_confidential}"
            ),
        )
        return Response(
            EvolutionFlowSerializer(
                evolution,
                context={"request": request, "patient": evolution.patient},
            ).data
        )

    @transaction.atomic
    def delete(self, request, pk):
        evolution = self.get_evolution(pk)
        if evolution.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(request, message="Você não pode arquivar esta evolução.")
        profile, _ = EvolutionClinicalData.objects.get_or_create(
            evolution=evolution,
            defaults={"updated_by": request.user},
        )
        profile.updated_by = request.user
        profile.save(update_fields=["updated_by", "updated_at"])
        profile.archive()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=f"Evolução #{evolution.id} arquivada logicamente",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PatientEvolutionAppointmentOptionsView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = (
            Appointment.objects.filter(patient=patient)
            .select_related("patient", "therapist")
            .order_by("-start_time")
        )
        if request.query_params.get("include_cancelled") != "true":
            queryset = queryset.exclude(status=Appointment.Status.CANCELLED)
        queryset = queryset.filter(evolution__isnull=True)[:100]
        return Response(EvolutionAppointmentOptionSerializer(queryset, many=True).data)


class EvolutionAttachmentListCreateView(ClinicalPatientMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, evolution_id):
        evolution = self.get_evolution(evolution_id)
        queryset = evolution.documents.filter(
            deleted_at__isnull=True,
            is_archived=False,
        ).order_by("created_at")
        return Response(
            EvolutionAttachmentSerializer(
                queryset,
                many=True,
                context={"request": request, "evolution": evolution},
            ).data
        )

    @transaction.atomic
    def post(self, request, evolution_id):
        evolution = self.get_evolution(evolution_id)
        profile = getattr(evolution, "clinical_data", None)
        if (
            evolution.created_by_id != request.user.id
            or not evolution.can_be_edited()
            or (profile and profile.status != EvolutionClinicalData.Status.DRAFT)
        ):
            self.permission_denied(request, message="Esta evolução não aceita novos anexos.")
        count = evolution.documents.filter(
            deleted_at__isnull=True,
            is_archived=False,
        ).count()
        if count >= max_evolution_attachments():
            return Response(
                {"file": ["O limite de anexos foi atingido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EvolutionAttachmentSerializer(
            data=request.data,
            context={"request": request, "evolution": evolution},
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=document,
            obj_repr=f"Anexo #{document.id} incluído na evolução #{evolution.id}",
        )
        return Response(
            EvolutionAttachmentSerializer(
                document,
                context={"request": request, "evolution": evolution},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class EvolutionAttachmentDetailView(ClinicalPatientMixin, APIView):
    def get_document(self, evolution_id, attachment_id):
        evolution = self.get_evolution(evolution_id)
        document = get_object_or_404(
            ClinicalDocument,
            pk=attachment_id,
            evolution=evolution,
            deleted_at__isnull=True,
        )
        return evolution, document

    @transaction.atomic
    def delete(self, request, evolution_id, attachment_id):
        evolution, document = self.get_document(evolution_id, attachment_id)
        profile = getattr(evolution, "clinical_data", None)
        if (
            evolution.created_by_id != request.user.id
            or not evolution.can_be_edited()
            or (profile and profile.status != EvolutionClinicalData.Status.DRAFT)
        ):
            self.permission_denied(request, message="Este anexo não pode mais ser removido.")
        document.soft_delete()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Anexo #{document.id} removido da evolução #{evolution.id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class EvolutionAttachmentDownloadView(EvolutionAttachmentDetailView):
    def get(self, request, evolution_id, attachment_id):
        evolution, document = self.get_document(evolution_id, attachment_id)
        if not can_view_confidential_evolution(request.user, evolution):
            self.permission_denied(request, message="Você não pode acessar este anexo.")
        try:
            stream = document.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Arquivo não encontrado no armazenamento.") from exc
        inline = request.query_params.get("inline") == "1" and document.content_type.startswith("image/")
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"Acesso ao anexo #{document.id} da evolução #{evolution.id}",
        )
        return FileResponse(
            stream,
            as_attachment=not inline,
            filename=document.original_name,
            content_type=document.content_type,
        )


class ClinicalEvolutionTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def _ensure_clinical_user(self, request):
        if request.user.is_secretary:
            self.permission_denied(request, message="Secretárias não acessam templates clínicos.")

    def get(self, request):
        self._ensure_clinical_user(request)
        queryset = ClinicalEvolutionTemplate.objects.filter(
            Q(owner=request.user) | Q(owner__isnull=True),
            is_active=True,
        ).select_related("owner")
        return Response(ClinicalEvolutionTemplateSerializer(queryset, many=True).data)

    def post(self, request):
        self._ensure_clinical_user(request)
        serializer = ClinicalEvolutionTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wants_system = bool(request.data.get("is_system"))
        if wants_system and not request.user.has_perm("records.manage_system_clinical_templates"):
            self.permission_denied(request, message="Você não pode criar templates globais.")
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
            self.permission_denied(request, message="Acesso clínico não permitido.")
        if template.owner_id not in (None, request.user.id):
            self.permission_denied(request, message="Template não autorizado.")
        if template.owner_id is None and not request.user.has_perm("records.manage_system_clinical_templates"):
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
