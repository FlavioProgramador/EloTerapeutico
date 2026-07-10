"""Resumo do prontuário com filtragem de documentos confidenciais."""

from __future__ import annotations

from django.db.models import Q

from apps.records.api.serializers.clinical_serializers import ClinicalDocumentSerializer
from apps.records.api.views.clinical_views import PatientRecordSummaryView
from apps.records.services.evolution_security import has_explicit_records_permission
from apps.records.treatment_models import ClinicalDocument


class SecurePatientRecordSummaryView(PatientRecordSummaryView):
    """Evita expor metadados de anexos confidenciais no workspace do paciente."""

    def get(self, request, patient_id):
        response = super().get(request, patient_id)
        patient = self.get_patient(patient_id)

        documents = ClinicalDocument.objects.filter(
            patient=patient,
            deleted_at__isnull=True,
            is_archived=False,
        ).select_related("evolution", "evolution__created_by", "uploaded_by")

        if not has_explicit_records_permission(request.user, "view_confidential_evolution"):
            documents = documents.filter(
                Q(evolution__isnull=True)
                | Q(evolution__is_confidential=False)
                | Q(evolution__created_by=request.user)
            )

        response.data["recent_documents"] = ClinicalDocumentSerializer(
            documents.order_by("-created_at")[:4],
            many=True,
            context={"request": request, "patient": patient},
        ).data
        return response
