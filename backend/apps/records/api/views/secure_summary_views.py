"""Resumo do prontuário com filtragem de conteúdo confidencial."""

from __future__ import annotations

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.response import Response

from apps.records.api.serializers.clinical_serializers import (
    ClinicalDocumentSerializer,
    TreatmentGoalSerializer,
)
from apps.records.api.views.clinical_views import PatientRecordSummaryView
from apps.records.models import Evolution
from apps.records.services.evolution_security import has_explicit_records_permission
from apps.records.treatment_models import ClinicalDocument, TreatmentGoal
from apps.scheduling.models import Appointment


class SecurePatientRecordSummaryView(PatientRecordSummaryView):
    """Evita expor registros ou metadados confidenciais no workspace."""

    def get(self, request, patient_id):
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

        now = timezone.now()
        next_appointment = (
            patient.appointments.filter(
                therapist=patient.therapist,
                start_time__gte=now,
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            )
            .order_by("start_time")
            .first()
        )
        previous_appointment = patient.appointments.filter(start_time__lt=now).order_by("-start_time").first()

        goals = (
            TreatmentGoal.objects.filter(
                patient=patient,
                status__in=[TreatmentGoal.Status.ACTIVE, TreatmentGoal.Status.PAUSED],
            )
            .select_related("created_by")
            .prefetch_related("evolutions")
            .distinct()[:4]
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

        payload = {
            "patient": {
                "id": patient.id,
                "full_name": patient.full_name,
                "age": patient.age,
                "phone": patient.phone,
                "email": patient.email,
                "status": patient.status,
                "status_display": patient.get_status_display(),
                "created_at": patient.created_at,
                "updated_at": patient.updated_at,
            },
            "sessions_total": evolutions.exclude(clinical_data__status="archived").count(),
            "treatment_start": (
                first_evolution.session_date
                if first_evolution
                else patient.created_at.date()
            ),
            "last_update": (
                latest_evolution.updated_at if latest_evolution else patient.updated_at
            ),
            "latest_evolution_id": latest_evolution.id if latest_evolution else None,
            "last_session": (previous_appointment.start_time if previous_appointment else None),
            "next_session": (
                {
                    "id": next_appointment.id,
                    "start_time": next_appointment.start_time,
                    "end_time": next_appointment.end_time,
                    "duration_minutes": next_appointment.duration_minutes,
                    "status": next_appointment.status,
                }
                if next_appointment
                else None
            ),
            "goals": TreatmentGoalSerializer(
                goals,
                many=True,
                context={"request": request, "patient": patient},
            ).data,
            "recent_documents": ClinicalDocumentSerializer(
                documents.order_by("-created_at")[:4],
                many=True,
                context={"request": request, "patient": patient},
            ).data,
            "ai_summary": {
                "available": False,
                "enabled": bool(getattr(settings, "CLINICAL_AI_ENABLED", False)),
                "message": "A integração de IA ainda não está configurada neste ambiente.",
            },
        }
        return Response(payload)
