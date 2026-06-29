"""Rotas do prontuário eletrônico."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .clinical_views import (
    AnamnesisVersionListView,
    ClinicalAiSummaryStatusView,
    ClinicalAnamnesisView,
    ClinicalDocumentDetailView,
    ClinicalDocumentDownloadView,
    ClinicalDocumentListCreateView,
    EvolutionDuplicateView,
    EvolutionWorkspaceDetailView,
    PatientEvolutionListCreateView,
    PatientRecordPdfView,
    PatientRecordSummaryView,
    TreatmentGoalDetailView,
    TreatmentGoalListCreateView,
)
from .finalize_views import EvolutionFinalizeFreshView
from .views import AnamnesisView, EvolutionViewSet

router = DefaultRouter()
router.register(r"evolutions", EvolutionViewSet, basename="evolution")

urlpatterns = [
    path("patients/<int:patient_id>/anamnesis/", AnamnesisView.as_view(), name="patient-anamnesis"),
    path("patients/<int:patient_id>/workspace/", PatientRecordSummaryView.as_view(), name="patient-record-workspace"),
    path("patients/<int:patient_id>/clinical-anamnesis/", ClinicalAnamnesisView.as_view(), name="clinical-anamnesis"),
    path("patients/<int:patient_id>/anamnesis-versions/", AnamnesisVersionListView.as_view(), name="anamnesis-versions"),
    path("patients/<int:patient_id>/clinical-evolutions/", PatientEvolutionListCreateView.as_view(), name="clinical-evolutions"),
    path("patients/<int:patient_id>/goals/", TreatmentGoalListCreateView.as_view(), name="treatment-goals"),
    path("patients/<int:patient_id>/documents/", ClinicalDocumentListCreateView.as_view(), name="clinical-documents"),
    path("patients/<int:patient_id>/export-pdf/", PatientRecordPdfView.as_view(), name="patient-record-pdf"),
    path("patients/<int:patient_id>/ai-summary/", ClinicalAiSummaryStatusView.as_view(), name="clinical-ai-summary"),
    path("clinical-evolutions/<int:pk>/", EvolutionWorkspaceDetailView.as_view(), name="clinical-evolution-detail"),
    path("clinical-evolutions/<int:pk>/finalize/", EvolutionFinalizeFreshView.as_view(), name="clinical-evolution-finalize"),
    path("clinical-evolutions/<int:pk>/duplicate/", EvolutionDuplicateView.as_view(), name="clinical-evolution-duplicate"),
    path("goals/<int:pk>/", TreatmentGoalDetailView.as_view(), name="treatment-goal-detail"),
    path("documents/<int:pk>/", ClinicalDocumentDetailView.as_view(), name="clinical-document-detail"),
    path("documents/<int:pk>/download/", ClinicalDocumentDownloadView.as_view(), name="clinical-document-download"),
    path("", include(router.urls)),
]
