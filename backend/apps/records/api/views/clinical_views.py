# mypy: ignore-errors
"""Endpoints da experiência integrada do prontuário eletrônico."""

from html import escape
from io import BytesIO

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

try:
    from weasyprint import HTML
except (ImportError, OSError):
    import logging

    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint could not import Pango/GObject libraries. Using dummy PDF fallback.")

    class HTML:
        def __init__(self, string=None, url_fetcher=None, **kwargs):
            self.string = string

        def write_pdf(self, target, **kwargs):
            dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
            if hasattr(target, "write"):
                target.write(dummy_pdf)
            else:
                with open(target, "wb") as f:
                    f.write(dummy_pdf)


from apps.agenda.models import Appointment
from apps.audit.services.access_logging import AuditLog, log_access
from apps.patients.models import Patient
from apps.patients.services.access_control import can_access_patient
from apps.records.api.serializers.clinical_serializers import (
    ClinicalAnamnesisSerializer,
    ClinicalDocumentSerializer,
    ClinicalExportSerializer,
    ClinicalFormResponseSerializer,
    EvolutionWorkspaceSerializer,
    TreatmentGoalSerializer,
)
from apps.records.extended_models import AnamnesisVersion, EvolutionClinicalData
from apps.records.models import Anamnesis, Evolution
from apps.records.treatment_models import (
    ClinicalDocument,
    ClinicalExport,
    ClinicalFormResponse,
    TreatmentGoal,
)


class RecordPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ClinicalPatientMixin:
    permission_classes = [IsAuthenticated]

    def get_patient(self, patient_id):
        patient = get_object_or_404(
            Patient.objects.select_related("therapist"),
            pk=patient_id,
        )
        user = self.request.user
        if not can_access_patient(user, patient, allow_secretary=False):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para acessar este prontuário.",
            )
        return patient

    def get_evolution(self, pk):
        evolution = get_object_or_404(
            Evolution.objects.select_related(
                "patient",
                "patient__therapist",
                "created_by",
                "clinical_data",
            ).prefetch_related("addenda"),
            pk=pk,
        )
        self.get_patient(evolution.patient_id)
        user = self.request.user
        # Validação de confidencialidade
        if (
            evolution.is_confidential
            and evolution.created_by_id != user.id
            and not user.has_perm("records.view_confidential_evolution")
        ):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para acessar esta evolução confidencial.",
            )
        return evolution

    @staticmethod
    def serialize_evolution(evolution, request):
        data = dict(EvolutionWorkspaceSerializer(evolution, context={"request": request}).data)
        clinical_data = getattr(evolution, "clinical_data", None)
        data.update(
            {
                "status": clinical_data.status if clinical_data else "draft",
                "status_display": (clinical_data.get_status_display() if clinical_data else "Rascunho"),
                "finalized_at": clinical_data.finalized_at if clinical_data else None,
                "archived_at": clinical_data.archived_at if clinical_data else None,
                "version_count": evolution.versions.count(),
            }
        )
        return data


class PatientRecordSummaryView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        evolutions = Evolution.objects.filter(patient=patient).select_related("clinical_data")
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
        goals = TreatmentGoal.objects.filter(
            patient=patient,
            status__in=[TreatmentGoal.Status.ACTIVE, TreatmentGoal.Status.PAUSED],
        )[:4]
        documents = ClinicalDocument.objects.filter(
            patient=patient,
            deleted_at__isnull=True,
            is_archived=False,
        )[:4]

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
            "treatment_start": (first_evolution.session_date if first_evolution else patient.created_at.date()),
            "last_update": (latest_evolution.updated_at if latest_evolution else patient.updated_at),
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
            "goals": TreatmentGoalSerializer(goals, many=True, context={"patient": patient}).data,
            "recent_documents": ClinicalDocumentSerializer(
                documents,
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


class ClinicalAnamnesisView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        anamnesis = Anamnesis.objects.filter(patient=patient).select_related("profile").first()
        if not anamnesis:
            return Response(
                {
                    "exists": False,
                    "patient": patient.id,
                    "completion_percentage": 0,
                    "version_count": 0,
                }
            )
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=anamnesis,
            obj_repr=f"Anamnese #{anamnesis.id}",
        )
        data = ClinicalAnamnesisSerializer(anamnesis).data
        data["exists"] = True
        return Response(data)

    def put(self, request, patient_id):
        return self._save(request, patient_id, partial=False)

    def patch(self, request, patient_id):
        return self._save(request, patient_id, partial=True)

    def _save(self, request, patient_id, partial):
        patient = self.get_patient(patient_id)
        serializer = ClinicalAnamnesisSerializer(
            data=request.data,
            partial=partial,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        anamnesis = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=anamnesis,
            obj_repr=f"Anamnese #{anamnesis.id}",
        )
        return Response(ClinicalAnamnesisSerializer(anamnesis).data)


class AnamnesisVersionListView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        versions = AnamnesisVersion.objects.filter(anamnesis__patient=patient).select_related("created_by")[:20]
        return Response(
            [
                {
                    "id": item.id,
                    "version": item.version,
                    "created_at": item.created_at,
                    "created_by": item.created_by.full_name,
                }
                for item in versions
            ]
        )


class PatientEvolutionListCreateView(ClinicalPatientMixin, APIView):
    pagination_class = RecordPagination

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = (
            Evolution.objects.filter(patient=patient)
            .select_related("created_by", "clinical_data")
            .prefetch_related("addenda", "versions")
            .order_by("-session_date", "-created_at")
        )

        # Filtro de confidencialidade
        user = request.user
        if not user.has_perm("records.view_confidential_evolution"):
            queryset = queryset.filter(Q(is_confidential=False) | Q(created_by=user))

        requested_status = request.query_params.get("status")
        if requested_status:
            queryset = queryset.filter(clinical_data__status=requested_status)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        data = [self.serialize_evolution(item, request) for item in page]
        return paginator.get_paginated_response(data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        session_date = request.data.get("session_date")
        if (
            session_date
            and Evolution.objects.filter(
                patient=patient,
                session_date=session_date,
                created_by=request.user,
            ).exists()
        ):
            return Response(
                {"session_date": ["Já existe uma evolução deste profissional para esta data."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = EvolutionWorkspaceSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=evolution,
            obj_repr=f"Evolução #{evolution.id}",
        )
        return Response(self.serialize_evolution(evolution, request), status=status.HTTP_201_CREATED)


class EvolutionWorkspaceDetailView(ClinicalPatientMixin, APIView):
    def get(self, request, pk):
        evolution = self.get_evolution(pk)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=evolution,
            obj_repr=f"Evolução #{evolution.id}",
        )
        return Response(self.serialize_evolution(evolution, request))

    def patch(self, request, pk):
        evolution = self.get_evolution(pk)
        serializer = EvolutionWorkspaceSerializer(
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
            obj_repr=f"Evolução #{evolution.id}",
        )
        return Response(self.serialize_evolution(evolution, request))


class EvolutionFinalizeView(ClinicalPatientMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        evolution = self.get_evolution(pk)
        if evolution.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(request, message="Somente o autor pode finalizar a evolução.")
        clinical_data, _ = EvolutionClinicalData.objects.get_or_create(
            evolution=evolution,
            defaults={"updated_by": request.user},
        )
        if clinical_data.status != EvolutionClinicalData.Status.DRAFT:
            return Response(
                {"detail": "A evolução já foi finalizada ou arquivada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (evolution.content.strip() or clinical_data.therapist_observations.strip()):
            return Response(
                {"detail": "Registre as observações clínicas antes de finalizar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        clinical_data.finalize()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=evolution,
            obj_repr=f"Evolução finalizada #{evolution.id}",
        )
        return Response(self.serialize_evolution(evolution, request))


class EvolutionDuplicateView(ClinicalPatientMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        source = self.get_evolution(pk)
        session_date = request.data.get("session_date")
        if not session_date:
            return Response(
                {"session_date": ["Informe a data da nova sessão."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        source_data = getattr(source, "clinical_data", None)
        payload = {
            "session_date": session_date,
            "session_time": request.data.get("session_time"),
            "duration_minutes": getattr(source_data, "duration_minutes", 50),
            "modality": getattr(source_data, "modality", "in_person"),
            "appointment_type": getattr(source_data, "appointment_type", "individual"),
            "interventions": getattr(source_data, "interventions", ""),
            "homework": getattr(source_data, "homework", ""),
            "next_steps": getattr(source_data, "next_steps", ""),
            "content": "Evolução criada a partir de um modelo anterior.",
        }
        serializer = EvolutionWorkspaceSerializer(
            data=payload,
            context={"request": request, "patient": source.patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.save()
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=evolution,
            obj_repr=f"Evolução duplicada #{evolution.id}",
        )
        return Response(self.serialize_evolution(evolution, request), status=status.HTTP_201_CREATED)


class TreatmentGoalListCreateView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = TreatmentGoal.objects.filter(patient=patient).prefetch_related("evolutions")
        requested_status = request.query_params.get("status")
        if requested_status:
            queryset = queryset.filter(status=requested_status)
        return Response(TreatmentGoalSerializer(queryset, many=True, context={"patient": patient}).data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        serializer = TreatmentGoalSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save(patient=patient, created_by=request.user)
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=goal,
            obj_repr=f"Meta terapêutica #{goal.id}",
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TreatmentGoalDetailView(ClinicalPatientMixin, APIView):
    def get_goal(self, pk):
        goal = get_object_or_404(TreatmentGoal.objects.prefetch_related("evolutions"), pk=pk)
        self.get_patient(goal.patient_id)
        return goal

    def patch(self, request, pk):
        goal = self.get_goal(pk)
        if goal.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(
                request,
                message="Somente o autor ou administrador pode alterar a meta.",
            )
        serializer = TreatmentGoalSerializer(
            goal,
            data=request.data,
            partial=True,
            context={"request": request, "patient": goal.patient},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=goal,
            obj_repr=f"Meta terapêutica #{goal.id}",
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        goal = self.get_goal(pk)
        if goal.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(
                request,
                message="Somente o autor ou administrador pode arquivar a meta.",
            )
        goal.archive()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=goal,
            obj_repr=f"Meta terapêutica arquivada #{goal.id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClinicalDocumentListCreateView(ClinicalPatientMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = ClinicalDocument.objects.filter(
            patient=patient,
            deleted_at__isnull=True,
        ).select_related("evolution", "uploaded_by")

        # Filtro de confidencialidade
        user = request.user
        if not user.has_perm("records.view_confidential_evolution"):
            queryset = queryset.filter(
                Q(evolution__isnull=True)
                | Q(evolution__is_confidential=False)
                | Q(evolution__created_by=user)
            )

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return Response(
            ClinicalDocumentSerializer(
                queryset,
                many=True,
                context={"request": request, "patient": patient},
            ).data
        )

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        serializer = ClinicalDocumentSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data.get("file")
        if not uploaded_file:
            return Response({"file": ["Selecione um arquivo."]}, status=status.HTTP_400_BAD_REQUEST)
        document = serializer.save(
            patient=patient,
            uploaded_by=request.user,
            original_name=uploaded_file.name[:255],
            content_type=uploaded_file.content_type,
            size_bytes=uploaded_file.size,
            checksum=ClinicalDocument.calculate_checksum(uploaded_file),
        )
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=document,
            obj_repr=f"Documento clínico #{document.id}",
        )
        return Response(
            ClinicalDocumentSerializer(
                document,
                context={"request": request, "patient": patient},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ClinicalDocumentDetailMixin(ClinicalPatientMixin):
    def get_document(self, pk):
        document = get_object_or_404(
            ClinicalDocument.objects.select_related("evolution"),
            pk=pk,
            deleted_at__isnull=True,
        )
        self.get_patient(document.patient_id)

        # Validação de confidencialidade da evolução vinculada
        if document.evolution_id and document.evolution.is_confidential:
            user = self.request.user
            if (
                document.evolution.created_by_id != user.id
                and not user.has_perm("records.view_confidential_evolution")
            ):
                self.permission_denied(
                    self.request,
                    message="Você não tem permissão para acessar documentos de uma evolução confidencial.",
                )
        return document


class ClinicalDocumentDetailView(ClinicalDocumentDetailMixin, APIView):
    def patch(self, request, pk):
        document = self.get_document(pk)
        serializer = ClinicalDocumentSerializer(
            document,
            data=request.data,
            partial=True,
            context={"request": request, "patient": document.patient},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento clínico #{document.id}",
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        document = self.get_document(pk)
        document.soft_delete()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento arquivado #{document.id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClinicalDocumentDownloadView(ClinicalDocumentDetailMixin, APIView):
    def get(self, request, pk):
        document = self.get_document(pk)
        try:
            stream = document.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Arquivo não encontrado no armazenamento.") from exc
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"Download do documento #{document.id}",
        )
        return FileResponse(
            stream,
            as_attachment=True,
            filename=document.original_name,
            content_type=document.content_type,
        )


class PatientRecordPdfView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)

        # Validar permissão distinta para exportar registros confidenciais
        other_confidential = (
            Evolution.objects.filter(patient=patient, is_confidential=True).exclude(created_by=request.user).exists()
        )
        if other_confidential and not request.user.has_perm("records.export_confidential_evolution"):
            self.permission_denied(
                request,
                message="Você não tem permissão para exportar evoluções confidenciais deste paciente.",
            )

        user = request.user
        queryset = Evolution.objects.filter(patient=patient).select_related(
            "created_by",
            "clinical_data",
        )
        if not user.has_perm("records.view_confidential_evolution"):
            queryset = queryset.filter(Q(is_confidential=False) | Q(created_by=user))

        from apps.records.services.utils import render_markdown_safely, safe_url_fetcher

        sections = []
        for evolution in queryset:
            clinical_data = getattr(evolution, "clinical_data", None)
            obs = getattr(clinical_data, "therapist_observations", "") or evolution.content
            interv = getattr(clinical_data, "interventions", "")
            steps = getattr(clinical_data, "next_steps", "")

            obs_html = render_markdown_safely(obs)
            interv_html = render_markdown_safely(interv)
            steps_html = render_markdown_safely(steps)

            sections.append(f"""
                <section>
                  <h2>{escape(evolution.session_date.strftime("%d/%m/%Y"))}</h2>
                  <p><strong>Profissional:</strong> {escape(evolution.created_by.full_name)}</p>
                  <div><strong>Observações clínicas:</strong> {obs_html}</div>
                  <div><strong>Intervenções:</strong> {interv_html}</div>
                  <div><strong>Próximos passos:</strong> {steps_html}</div>
                </section>
                """)

        html = f"""
        <html><head><meta charset='utf-8'><style>
        body{{font-family:Arial,sans-serif;color:#17201d;font-size:12px}}
        h1{{color:#0f766e}} section{{border-top:1px solid #d8e0dd;padding:14px 0}}
        p{{line-height:1.5;white-space:pre-wrap}}
        div{{margin-top:4px}}
        </style></head><body>
        <h1>Prontuário eletrônico</h1>
        <p><strong>Paciente:</strong> {escape(patient.full_name)}</p>
        <p><strong>Gerado em:</strong> {timezone.localtime():%d/%m/%Y %H:%M}</p>
        {"".join(sections) or "<p>Nenhuma evolução registrada.</p>"}
        </body></html>
        """
        output = BytesIO()
        HTML(string=html, url_fetcher=safe_url_fetcher).write_pdf(output)
        output.seek(0)
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=patient,
            obj_repr=f"Exportação do prontuário #{patient.id}",
        )
        return FileResponse(
            output,
            as_attachment=True,
            filename=f"prontuario-paciente-{patient.id}.pdf",
            content_type="application/pdf",
        )


class ClinicalAiSummaryStatusView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        return Response(
            {
                "patient": patient.id,
                "available": False,
                "enabled": bool(getattr(settings, "CLINICAL_AI_ENABLED", False)),
                "status": "not_configured",
                "message": "Resumo assistido indisponível até a configuração de um provedor seguro e consentimento adequado.",
            }
        )


class ClinicalFormResponseListCreateView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = ClinicalFormResponse.objects.filter(patient=patient).order_by("-completed_at", "-created_at")

        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(form_name__icontains=search)

        serializer = ClinicalFormResponseSerializer(queryset, many=True)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=patient,
            obj_repr=f"Lista de formulários do paciente #{patient.id}",
        )
        return Response(serializer.data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        serializer = ClinicalFormResponseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(patient=patient, therapist=request.user)
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=instance,
            obj_repr=f"Resposta de formulário #{instance.id}",
        )
        return Response(
            ClinicalFormResponseSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


class ClinicalFormResponseDetailView(ClinicalPatientMixin, APIView):
    def get(self, request, pk):
        response_obj = get_object_or_404(ClinicalFormResponse, pk=pk)
        self.get_patient(response_obj.patient_id)
        serializer = ClinicalFormResponseSerializer(response_obj)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=response_obj,
            obj_repr=f"Resposta de formulário #{response_obj.id}",
        )
        return Response(serializer.data)


class ClinicalExportListCreateView(ClinicalPatientMixin, APIView):
    def get(self, request, patient_id):
        if request.user.is_secretary:
            self.permission_denied(
                request,
                message="Secretárias não possuem acesso a exportações clínicas.",
            )
        patient = self.get_patient(patient_id)
        queryset = ClinicalExport.objects.filter(patient=patient).order_by("-created_at")

        if not request.user.is_admin_role:
            queryset = queryset.filter(created_by=request.user)

        serializer = ClinicalExportSerializer(queryset, many=True)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=patient,
            obj_repr=f"Lista de exportações do paciente #{patient.id}",
        )
        return Response(serializer.data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)

        # Validar permissão distinta para exportar registros confidenciais
        other_confidential = (
            Evolution.objects.filter(patient=patient, is_confidential=True).exclude(created_by=request.user).exists()
        )
        if other_confidential and not request.user.has_perm("records.export_confidential_evolution"):
            self.permission_denied(
                request,
                message="Você não tem permissão para exportar evoluções confidenciais deste paciente.",
            )

        serializer = ClinicalExportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Sanitização do nome do arquivo
        from django.utils.text import slugify

        clean_name = slugify(patient.full_name)[:50]
        filename = f"prontuario_{clean_name}_{timezone.now():%Y%m%d%H%M%S}.pdf"

        instance = serializer.save(
            patient=patient,
            created_by=request.user,
            filename=filename,
            status=ClinicalExport.Status.PENDING,
        )

        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=patient,
            obj_repr=f"Solicitação de exportação #{instance.id}",
        )
        return Response(ClinicalExportSerializer(instance).data, status=status.HTTP_201_CREATED)


class ClinicalExportRetryView(ClinicalPatientMixin, APIView):
    def post(self, request, pk):
        export_obj = get_object_or_404(ClinicalExport, pk=pk)
        self.get_patient(export_obj.patient_id)

        if export_obj.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(
                request,
                message="Você não tem permissão para gerenciar esta exportação.",
            )

        if export_obj.status not in [
            ClinicalExport.Status.FAILED,
            ClinicalExport.Status.EXPIRED,
        ]:
            return Response(
                {"detail": "Somente exportações com status Falhou ou Expirado podem ser reprocessadas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        export_obj.status = ClinicalExport.Status.PENDING
        export_obj.retries = 0
        export_obj.started_at = None
        export_obj.completed_at = None
        export_obj.worker_id = ""
        export_obj.error_message = ""
        export_obj.save()

        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=export_obj.patient,
            obj_repr=f"Reprocessamento de exportação #{export_obj.id}",
        )
        return Response(ClinicalExportSerializer(export_obj).data)


class ClinicalExportDownloadView(ClinicalPatientMixin, APIView):
    def get(self, request, pk):
        export_obj = get_object_or_404(ClinicalExport, pk=pk)
        self.get_patient(export_obj.patient_id)

        if export_obj.created_by_id != request.user.id and not request.user.is_admin_role:
            self.permission_denied(
                request,
                message="Você não tem permissão para baixar esta exportação.",
            )

        if export_obj.status != ClinicalExport.Status.COMPLETED:
            return Response(
                {"detail": "O arquivo de exportação ainda não está pronto ou falhou."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not export_obj.file:
            raise Http404("Arquivo de exportação não encontrado.")

        try:
            stream = export_obj.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Arquivo físico de exportação não encontrado.") from exc

        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=export_obj.patient,
            obj_repr=f"Download da exportação #{export_obj.id}",
        )
        return FileResponse(
            stream,
            as_attachment=True,
            filename=export_obj.filename,
            content_type="application/pdf",
        )
