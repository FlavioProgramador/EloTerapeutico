from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from core.audit import AuditLog, log_access
from .dashboard_serializers import PatientDashboardSerializer


class PatientDashboardActions:
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

    @action(detail=True, methods=["get"], url_path="dashboard")
    def dashboard(self, request, pk=None):
        patient = self.get_object()
        latest_evolution = patient.evolutions.order_by(
            "-session_date", "-created_at"
        ).first()
        documents = patient.clinical_documents.filter(
            is_archived=False
        ).order_by("-created_at")[:3]
        next_appointment = patient.appointments.filter(
            start_time__gte=timezone.now(),
            status__in=["scheduled", "confirmed"],
        ).order_by("start_time").first()
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
                    patient, context={"request": request}
                ).data,
                "next_session": None if not next_appointment else {
                    "id": next_appointment.id,
                    "start_time": next_appointment.start_time,
                    "end_time": next_appointment.end_time,
                    "status": next_appointment.status,
                },
                "latest_evolution": None if not latest_evolution else {
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
