import csv
import re
from datetime import timedelta
from io import StringIO

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.services.access_logging import AuditLog, log_access
from apps.patients.api.serializers.dashboard_serializers import PatientDashboardSerializer
from apps.patients.api.serializers.form_serializers import PatientFormSerializer
from apps.patients.api.serializers.legacy_serializers import PatientDetailSerializer

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
                {
                    "detail": (
                        "A importação em lote está disponível somente para terapeutas. "
                        "Cadastros administrativos devem informar o profissional "
                        "responsável individualmente."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        uploaded = request.FILES.get("file")
        confirm = str(request.data.get("confirm", "false")).lower() == "true"
        if not uploaded:
            return Response({"detail": "Envie um arquivo CSV."}, status=400)
        if uploaded.size > 2 * 1024 * 1024:
            return Response({"detail": "O arquivo deve possuir até 2 MB."}, status=400)

        try:
            content = uploaded.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "Utilize um CSV codificado em UTF-8."},
                status=400,
            )

        reader = csv.DictReader(StringIO(content))
        required_columns = {"full_name", "cpf", "birth_date"}
        fieldnames = set(reader.fieldnames or [])
        if not required_columns.issubset(fieldnames):
            return Response(
                {"detail": ("O CSV deve conter as colunas full_name, cpf e birth_date.")},
                status=400,
            )

        rows = list(reader)
        if not rows:
            return Response(
                {"detail": "O arquivo CSV não possui registros."},
                status=400,
            )
        if len(rows) > 500:
            return Response(
                {"detail": "Importe no máximo 500 pacientes por vez."},
                status=400,
            )

        valid_payloads = []
        errors = []
        duplicates = []
        seen_cpfs = set()

        for line, row in enumerate(rows, start=2):
            raw_cpf = _csv_cell(row, "cpf")
            clean_cpf = re.sub(r"\D", "", raw_cpf)
            if clean_cpf and (clean_cpf in seen_cpfs or Patient.all_objects.filter(cpf=clean_cpf).exists()):
                duplicates.append({"line": line, "cpf": raw_cpf})
                continue
            if clean_cpf:
                seen_cpfs.add(clean_cpf)

            payload = {
                "full_name": _csv_cell(row, "full_name"),
                "cpf": raw_cpf,
                "birth_date": _csv_cell(row, "birth_date"),
                "email": _csv_cell(row, "email"),
                "phone": _csv_cell(row, "phone"),
                "gender": _csv_cell(row, "gender", "N") or "N",
                "status": _csv_cell(row, "status", "active") or "active",
                "modality": (_csv_cell(row, "modality", "in_person") or "in_person"),
                "payer_type": (_csv_cell(row, "payer_type", "private") or "private"),
                "therapist": request.user.pk,
            }

            serializer = PatientFormSerializer(
                data=payload,
                context={"request": request},
            )
            if serializer.is_valid():
                valid_payloads.append(serializer.validated_data)
            else:
                errors.append({"line": line, "errors": serializer.errors})

        preview = {
            "total": len(rows),
            "valid": len(valid_payloads),
            "duplicates": duplicates,
            "errors": errors,
            "ready": not errors and not duplicates,
        }
        if not confirm or errors or duplicates:
            return Response(preview)

        with transaction.atomic():
            for payload in valid_payloads:
                Patient.objects.create(**payload)

        log_access(
            request,
            AuditLog.Action.CREATE,
            obj_repr=f"Importação de {len(valid_payloads)} pacientes",
        )
        return Response(
            {**preview, "imported": len(valid_payloads)},
            status=status.HTTP_201_CREATED,
        )

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
