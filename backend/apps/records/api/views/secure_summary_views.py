"""Resumo do prontuário com filtragem de conteúdo confidencial."""

from __future__ import annotations

from django.db.models import Q

from apps.records.api.serializers.clinical_serializers import ClinicalDocumentSerializer
from apps.records.api.views.clinical_views import PatientRecordSummaryView
from apps.records.models import Evolution
from apps.records.services.evolution_security import has_explicit_records_permission
from apps.records.treatment_models import ClinicalDocument


class SecurePatientRecordSummaryView(PatientRecordSummaryView):
    """Evita expor registros ou metadados confidenciais no workspace."""

    def get(self, request, patient_id):
        response = super().get(request, patient_id)
        patient = self.get_patient(patient_id)
        can_view_all_confidential = has_explicit_records_permission(
            request.user,
            "view_confidential_evolution",
        )

        evolutions = Evolution.objects.filter(patient=patient).select_related("clinical_data")
        if not can_view_all_confidential:
            evolutions = evolutions.filter(
                Q(is_confidential=False) | Q(created_by=request.user)
            )

        latest_evolution = evolutions.order_by("-session_date", "-created_at").first()
        first_evolution = evolutions.order_by("session_date", "created_at").first()
        response.data["sessions_total"] = evolutions.exclude(
            clinical_data__status="archived"
        ).count()
        response.data["treatment_start"] = (
            first_evolution.session_date
            if first_evolution
            else patient.created_at.date()
        )
        response.data["last_update"] = (
            latest_evolution.updated_at if latest_evolution else patient.updated_at
        )
        response.data["latest_evolution_id"] = (
            latest_evolution.id if latest_evolution else None
        )

        documents = ClinicalDocument.objects.filter(
            patient=patient,
            deleted_at__isnull=True,
            is_archived=False,
        ).select_related("evolution", "evolution__created_by", "uploaded_by")
        if not can_view_all_confidential:
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
