"""Processamento persistente e idempotente de exportações clínicas."""

from __future__ import annotations

import hashlib
import logging
from datetime import timedelta
from html import escape
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.utils import timezone

from apps.records.models import Evolution
from apps.records.services.evolution_security import has_explicit_records_permission
from apps.records.services.utils import render_markdown_safely, safe_url_fetcher
from apps.records.treatment_models import ClinicalExport

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML
except (ImportError, OSError):
    HTML = None


class ExportProcessingError(RuntimeError):
    """Falha segura durante a geração do arquivo de exportação."""


def _render_export_html(export_obj: ClinicalExport) -> str:
    patient = export_obj.patient
    requester = export_obj.created_by
    evolutions = (
        Evolution.objects.filter(patient=patient)
        .select_related("created_by", "clinical_data")
        .order_by("session_date", "created_at")
    )
    if not has_explicit_records_permission(requester, "view_confidential_evolution"):
        evolutions = evolutions.filter(models.Q(is_confidential=False) | models.Q(created_by=requester))

    sections: list[str] = []
    for evolution in evolutions.iterator(chunk_size=100):
        clinical_data = getattr(evolution, "clinical_data", None)
        observations = getattr(clinical_data, "therapist_observations", "") or evolution.content
        interventions = getattr(clinical_data, "interventions", "")
        next_steps = getattr(clinical_data, "next_steps", "")
        sections.append(
            f"""
            <section>
              <h2>Sessão em {evolution.session_date:%d/%m/%Y}</h2>
              <p><strong>Profissional:</strong> {escape(evolution.created_by.full_name)}</p>
              <div><strong>Observações clínicas:</strong> {render_markdown_safely(observations)}</div>
              <div><strong>Intervenções:</strong> {render_markdown_safely(interventions)}</div>
              <div><strong>Próximos passos:</strong> {render_markdown_safely(next_steps)}</div>
            </section>
            """
        )

    return f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{ font-family: Arial, sans-serif; color: #17201d; font-size: 12px; line-height: 1.5; }}
          h1 {{ color: #0f766e; border-bottom: 2px solid #0f766e; padding-bottom: 8px; }}
          h2 {{ color: #0f766e; margin-bottom: 5px; }}
          section {{ margin-bottom: 20px; border-bottom: 1px solid #d8e0dd; padding-bottom: 15px; }}
          p {{ margin: 4px 0; }}
        </style>
      </head>
      <body>
        <h1>Prontuário Clínico Completo</h1>
        <p><strong>Paciente:</strong> {escape(patient.full_name)}</p>
        <p><strong>Terapeuta responsável:</strong> {escape(patient.therapist.full_name)}</p>
        <p><strong>Gerado em:</strong> {timezone.localtime():%d/%m/%Y %H:%M}</p>
        <p><strong>Solicitado por:</strong> {escape(requester.full_name)}</p>
        <div>{"".join(sections) or "<p>Nenhum registro clínico encontrado.</p>"}</div>
      </body>
    </html>
    """


def _generate_pdf(export_obj: ClinicalExport) -> bytes:
    if HTML is None:
        raise ExportProcessingError("O mecanismo de geração de PDF não está disponível.")
    output = BytesIO()
    HTML(string=_render_export_html(export_obj), url_fetcher=safe_url_fetcher).write_pdf(output)
    return output.getvalue()


def claim_export(export_id: int, *, task_id: str) -> ClinicalExport | None:
    """Reserva uma exportação; chamadas repetidas não duplicam arquivos concluídos."""

    with transaction.atomic():
        export_obj = (
            ClinicalExport.objects.select_for_update()
            .select_related("patient", "patient__therapist", "created_by")
            .get(pk=export_id)
        )
        if export_obj.status in {
            ClinicalExport.Status.COMPLETED,
            ClinicalExport.Status.EXPIRED,
            ClinicalExport.Status.CANCELLED,
        }:
            return None
        if export_obj.status not in {ClinicalExport.Status.PENDING, ClinicalExport.Status.PROCESSING}:
            return None
        processing_timeout = timezone.now() - timedelta(
            minutes=max(int(getattr(settings, "CLINICAL_EXPORT_PROCESSING_TIMEOUT_MINUTES", 15)), 1)
        )
        if (
            export_obj.status == ClinicalExport.Status.PROCESSING
            and export_obj.worker_id
            and export_obj.worker_id != task_id
            and export_obj.started_at
            and export_obj.started_at > processing_timeout
        ):
            return None
        export_obj.status = ClinicalExport.Status.PROCESSING
        export_obj.started_at = timezone.now()
        export_obj.completed_at = None
        export_obj.next_attempt_at = None
        export_obj.worker_id = task_id[:255]
        export_obj.progress = 10
        export_obj.error_code = ""
        export_obj.error_message = ""
        export_obj.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "next_attempt_at",
                "worker_id",
                "progress",
                "error_code",
                "error_message",
            ]
        )
        return export_obj


def process_clinical_export(export_id: int, *, task_id: str) -> int:
    export_obj = claim_export(export_id, task_id=task_id)
    if export_obj is None:
        return export_id

    pdf_data = _generate_pdf(export_obj)
    checksum = hashlib.sha256(pdf_data).hexdigest()
    retention_hours = max(int(getattr(settings, "CLINICAL_EXPORT_RETENTION_HOURS", 24)), 1)

    with transaction.atomic():
        locked = ClinicalExport.objects.select_for_update().get(pk=export_id)
        if locked.status == ClinicalExport.Status.CANCELLED:
            return export_id
        if locked.file:
            locked.file.delete(save=False)
        locked.file.save(locked.filename, ContentFile(pdf_data), save=False)
        locked.size_bytes = len(pdf_data)
        locked.content_type = "application/pdf"
        locked.checksum_sha256 = checksum
        locked.status = ClinicalExport.Status.COMPLETED
        locked.progress = 100
        locked.completed_at = timezone.now()
        locked.expires_at = locked.completed_at + timedelta(hours=retention_hours)
        locked.download_url = f"/api/v1/records/exports/{locked.id}/download/"
        locked.next_attempt_at = None
        locked.error_code = ""
        locked.error_message = ""
        locked.metadata = {
            **(locked.metadata or {}),
            "storage_key": locked.file.name,
            "generated_by": "celery",
        }
        locked.save()

    logger.info(
        "clinical_export_completed",
        extra={"export_id": export_id, "task_id": task_id, "size_bytes": len(pdf_data)},
    )
    return export_id


def register_export_failure(
    export_id: int,
    *,
    exception: Exception,
    final: bool,
    retry_in_seconds: int | None = None,
) -> None:
    now = timezone.now()
    with transaction.atomic():
        export_obj = ClinicalExport.objects.select_for_update().get(pk=export_id)
        if export_obj.status in {
            ClinicalExport.Status.COMPLETED,
            ClinicalExport.Status.EXPIRED,
            ClinicalExport.Status.CANCELLED,
        }:
            return
        export_obj.retries += 1
        export_obj.progress = 0
        export_obj.worker_id = ""
        export_obj.error_code = exception.__class__.__name__[:80]
        export_obj.error_message = "Falha interna ao gerar a exportação."
        if final:
            export_obj.status = ClinicalExport.Status.FAILED
            export_obj.completed_at = now
            export_obj.next_attempt_at = None
        else:
            export_obj.status = ClinicalExport.Status.PENDING
            export_obj.started_at = None
            export_obj.next_attempt_at = now + timedelta(seconds=max(retry_in_seconds or 30, 1))
        export_obj.save()

    logger.warning(
        "clinical_export_failed",
        extra={
            "export_id": export_id,
            "exception_type": exception.__class__.__name__,
            "final": final,
        },
    )
