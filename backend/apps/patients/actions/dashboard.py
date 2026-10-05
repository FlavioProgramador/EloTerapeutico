import csv
import re
from datetime import timedelta
from io import StringIO

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.organizations.services.tenant_context import ensure_request_organization
from apps.patients.api.serializers.dashboard_serializers import PatientDashboardSerializer
from apps.patients.api.serializers.form_serializers import PatientFormSerializer
from apps.patients.api.serializers.legacy_serializers import PatientDetailSerializer
from apps.patients.services.imports import PatientImportError, import_patients_from_csv

from ..models import Patient
from .forms import PatientFormActions
from .invites import PatientInviteActions


def _csv_cell(row, key, default=""):
    value = row.get(key, default)
    if value is None:
        return default
    return str(value).strip()


class PatientDashboardActions(PatientInviteActions, PatientFormActions):
    @action(detail=False, methods=["get"], url_path="dashboard-metrics")
    def dashboard_metrics(self, request):
        queryset = self.get_queryset()
        today = timezone.localdate()
        current_month = today.replace(day=1)
        previous_month_end = current_month - timedelta(days=1)
        previous_month = previous_month_end.replace(day=1)
        total = queryset.count()
        active = queryset.filter(status="active").count()
        discharged = queryset.filter(status__in=["discharged", "inactive"]).count()
        new_current = queryset.filter(created_at__date__gte=current_month).count()
        new_previous = queryset.filter(
            created_at__date__gte=previous_month,
            created_at__date__lte=previous_month_end,
        ).count()
        return Response(
            {
                "total": total,
                "active": active,
                "active_percentage": round(active / total * 100) if total else 0,
                "discharged": discharged,
                "discharged_percentage": round(discharged / total * 100) if total else 0,
                "new_current_month": new_current,
                "new_previous_month": new_previous,
            }
        )

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        if not request.user.is_therapist:
            return Response(
                {"detail": "Operação permitida somente para terapeutas."},
                status=status.HTTP_403_FORBIDDEN,
            )
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response(
                {"detail": "Envie um arquivo CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        organization, _ = ensure_request_organization(
            request=request,
            required=True,
        )
        try:
            result = import_patients_from_csv(
                uploaded_file=uploaded,
                therapist=request.user,
                organization=organization,
                confirm=str(request.data.get("confirm", "false")).lower() == "true",
            )
        except PatientImportError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if result.imported:
            log_access(
                request,
                AuditLog.Action.CREATE,
                obj_repr=f"Importação de {result.imported} pacientes",
            )
        response_status = status.HTTP_201_CREATED if result.imported else status.HTTP_200_OK
        return Response(result.as_dict(), status=response_status)

    @action(detail=True, methods=["get"], url_path="form")
    def form(self, request, pk=None):
        patient = self.get_object()
        detail_data = PatientDetailSerializer(
            patient,
            context={"request": request},
        ).data
        form_data = PatientFormSerializer(
            patient,
            context={"request": request},
        ).data
        return Response({**detail_data, **form_data})

    @action(detail=True, methods=["get"], url_path="dashboard")
    def dashboard(self, request, pk=None):
        patient = self.get_object()
        can_access_records = request.user.is_therapist or request.user.is_admin_role

        latest_evolution = None
        documents = []
        if can_access_records:
            latest_evolution = patient.evolutions.order_by(
                "-session_date",
                "-created_at",
            ).first()
            documents = list(patient.clinical_documents.filter(is_archived=False).order_by("-created_at")[:3])

        next_appointment = (
            patient.appointments.filter(
                start_time__gte=timezone.now(),
                status__in=["scheduled", "confirmed"],
            )
            .order_by("start_time")
            .first()
        )
        total = getattr(patient, "total_sessions", 0)
        missed = getattr(patient, "missed_sessions", 0)
        attendance = round((total - missed) / total * 100) if total else None
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=patient,
            obj_repr=f"Paciente #{patient.pk}",
        )
        return Response(
            {
                "patient": PatientDashboardSerializer(
                    patient,
                    context={"request": request},
                ).data,
                "can_access_records": can_access_records,
                "next_session": None
                if not next_appointment
                else {
                    "id": next_appointment.id,
                    "start_time": next_appointment.start_time,
                    "end_time": next_appointment.end_time,
                    "status": next_appointment.status,
                },
                "latest_evolution": None
                if not latest_evolution
                else {
                    "id": latest_evolution.id,
                    "session_date": latest_evolution.session_date,
                    "summary": latest_evolution.content[:280],
                    "is_locked": latest_evolution.is_locked,
                },
                "recent_documents": [
                    {
                        "id": document.id,
                        "name": document.original_name,
                        "category": document.get_category_display(),
                        "created_at": document.created_at,
                    }
                    for document in documents
                ],
                "follow_up": {
                    "total_sessions": total,
                    "missed_sessions": missed,
                    "attendance_percentage": attendance,
                    "active_goals": getattr(patient, "active_goals_count", 0),
                },
                "ai_summary": {
                    "available": False,
                    "message": "Integração de IA ainda não configurada.",
                },
            }
        )
