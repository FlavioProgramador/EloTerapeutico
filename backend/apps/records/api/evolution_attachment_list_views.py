"""Listagem e criação de anexos de evoluções clínicas."""

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import AuditLog, log_access

from ..clinical_views import ClinicalPatientMixin
from ..evolution_security import max_evolution_attachments
from ..selectors.evolutions import active_evolution_attachments
from .evolution_attachment_serializers import EvolutionAttachmentSerializer


class EvolutionAttachmentListCreateView(ClinicalPatientMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, evolution_id):
        evolution = self.get_evolution(evolution_id)
        queryset = active_evolution_attachments(evolution=evolution)
        serializer = EvolutionAttachmentSerializer(
            queryset,
            many=True,
            context={"request": request, "evolution": evolution},
        )
        return Response(serializer.data)

    def post(self, request, evolution_id):
        evolution = self.get_evolution(evolution_id)
        attachment_count = active_evolution_attachments(
            evolution=evolution
        ).count()
        if attachment_count >= max_evolution_attachments():
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
        output = EvolutionAttachmentSerializer(
            document,
            context={"request": request, "evolution": evolution},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)
