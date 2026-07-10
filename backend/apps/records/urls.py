"""Rotas do prontuário eletrônico."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.records.api.views.clinical_views import (
    AnamnesisVersionListView,
    ClinicalAiSummaryStatusView,
    ClinicalAnamnesisView,
    ClinicalExportDownloadView,
    ClinicalExportListCreateView,
    ClinicalExportRetryView,
    ClinicalFormResponseDetailView,
    ClinicalFormResponseListCreateView,
    EvolutionDuplicateView,
    PatientRecordPdfView,
    PatientRecordSummaryView,
    TreatmentGoalDetailView,
    TreatmentGoalListCreateView,
)
from apps.records.api.views.finalize_views import EvolutionFinalizeFreshView
from apps.records.api.views.legacy_views import AnamnesisView, EvolutionViewSet
from apps.records.api.views.secure_document_views import (
    SecureClinicalDocumentDetailView,
    SecureClinicalDocumentDownloadView,
    SecureClinicalDocumentListCreateView,
)

from .api.evolution_attachment_detail_views import (
    EvolutionAttachmentDetailView,
    EvolutionAttachmentDownloadView,
)
from .api.evolution_attachment_list_views import EvolutionAttachmentListCreateView
from .api.evolution_template_views import (
    ClinicalEvolutionTemplateDetailView,
    ClinicalEvolutionTemplateListCreateView,
)
from .api.evolution_views import (
    EvolutionFlowDetailView,
    PatientEvolutionAppointmentOptionsView,
    PatientEvolutionFlowView,
)

router = DefaultRouter()
router.register(r"evolutions", EvolutionViewSet, basename="evolution")

urlpatterns = [
    path(
        "patients/<int:patient_id>/anamnesis/",
        AnamnesisView.as_view(),
        name="patient-anamnesis",
    ),
    path(
        "patients/<int:patient_id>/workspace/",
        PatientRecordSummaryView.as_view(),
        name="patient-record-workspace",
    ),
    path(
        "patients/<int:patient_id>/clinical-anamnesis/",
        ClinicalAnamnesisView.as_view(),
        name="clinical-anamnesis",
    ),
    path(
        "patients/<int:patient_id>/anamnesis-versions/",
        AnamnesisVersionListView.as_view(),
        name="anamnesis-versions",
    ),
    path(
        "patients/<int:patient_id>/clinical-evolutions/",
        PatientEvolutionFlowView.as_view(),
        name="clinical-evolutions",
    ),
    path(
        "patients/<int:patient_id>/evolution-appointments/",
        PatientEvolutionAppointmentOptionsView.as_view(),
        name="evolution-appointment-options",
    ),
    path(
        "patients/<int:patient_id>/goals/",
        TreatmentGoalListCreateView.as_view(),
        name="treatment-goals",
    ),
    path(
        "patients/<int:patient_id>/documents/",
        SecureClinicalDocumentListCreateView.as_view(),
        name="clinical-documents",
    ),
    path(
        "patients/<int:patient_id>/export-pdf/",
        PatientRecordPdfView.as_view(),
        name="patient-record-pdf",
    ),
    path(
        "patients/<int:patient_id>/ai-summary/",
        ClinicalAiSummaryStatusView.as_view(),
        name="clinical-ai-summary",
    ),
    path(
        "patients/<int:patient_id>/forms/",
        ClinicalFormResponseListCreateView.as_view(),
        name="patient-forms",
    ),
    path(
        "forms/<int:pk>/",
        ClinicalFormResponseDetailView.as_view(),
        name="form-response-detail",
    ),
    path(
        "patients/<int:patient_id>/exports/",
        ClinicalExportListCreateView.as_view(),
        name="patient-exports",
    ),
    path(
        "exports/<int:pk>/retry/",
        ClinicalExportRetryView.as_view(),
        name="export-retry",
    ),
    path(
        "exports/<int:pk>/download/",
        ClinicalExportDownloadView.as_view(),
        name="export-download",
    ),
    path(
        "clinical-evolutions/<int:pk>/",
        EvolutionFlowDetailView.as_view(),
        name="clinical-evolution-detail",
    ),
    path(
        "clinical-evolutions/<int:pk>/finalize/",
        EvolutionFinalizeFreshView.as_view(),
        name="clinical-evolution-finalize",
    ),
    path(
        "clinical-evolutions/<int:pk>/duplicate/",
        EvolutionDuplicateView.as_view(),
        name="clinical-evolution-duplicate",
    ),
    path(
        "clinical-evolutions/<int:evolution_id>/attachments/",
        EvolutionAttachmentListCreateView.as_view(),
        name="clinical-evolution-attachments",
    ),
    path(
        "clinical-evolutions/<int:evolution_id>/attachments/<int:attachment_id>/",
        EvolutionAttachmentDetailView.as_view(),
        name="clinical-evolution-attachment-detail",
    ),
    path(
        "clinical-evolutions/<int:evolution_id>/attachments/<int:attachment_id>/download/",
        EvolutionAttachmentDownloadView.as_view(),
        name="clinical-evolution-attachment-download",
    ),
    path(
        "clinical-templates/",
        ClinicalEvolutionTemplateListCreateView.as_view(),
        name="clinical-evolution-templates",
    ),
    path(
        "clinical-templates/<int:pk>/",
        ClinicalEvolutionTemplateDetailView.as_view(),
        name="clinical-evolution-template-detail",
    ),
    path(
        "goals/<int:pk>/",
        TreatmentGoalDetailView.as_view(),
        name="treatment-goal-detail",
    ),
    path(
        "documents/<int:pk>/",
        SecureClinicalDocumentDetailView.as_view(),
        name="clinical-document-detail",
    ),
    path(
        "documents/<int:pk>/download/",
        SecureClinicalDocumentDownloadView.as_view(),
        name="clinical-document-download",
    ),
    path("", include(router.urls)),
]
