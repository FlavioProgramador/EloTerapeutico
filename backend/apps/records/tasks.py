"""Tarefas Celery do domínio de exportações e uploads clínicos."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from celery.utils import uuid as celery_uuid
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.records.services.clinical_document_scanning import (
    ClinicalDocumentQuarantineMissing,
    process_clinical_document_scan,
    register_document_scan_failure,
)
from apps.records.services.export_processing import process_clinical_export, register_export_failure
from apps.records.services.malware_scanning import MalwareScannerProtocolError, MalwareScannerUnavailable
from apps.records.treatment_models import ClinicalDocument, ClinicalExport

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="apps.records.tasks.scan_clinical_document",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
    max_retries=3,
    soft_time_limit=60,
    time_limit=90,
)
def scan_clinical_document(self, document_id: int) -> None:
    """Analisa um arquivo em quarentena e libera somente resultados limpos."""

    try:
        process_clinical_document_scan(document_id)
    except ClinicalDocumentQuarantineMissing as exc:
        register_document_scan_failure(document_id, exc)
        raise
    except (MalwareScannerUnavailable, MalwareScannerProtocolError, SoftTimeLimitExceeded) as exc:
        register_document_scan_failure(document_id, exc)
        if self.request.retries >= self.max_retries:
            raise
        countdown = min(30 * (2**self.request.retries), 300)
        raise self.retry(exc=exc, countdown=countdown, max_retries=self.max_retries)
    except Exception as exc:
        register_document_scan_failure(document_id, exc)
        if self.request.retries >= self.max_retries:
            raise
        countdown = min(30 * (2**self.request.retries), 300)
        raise self.retry(exc=exc, countdown=countdown, max_retries=self.max_retries)


@shared_task(
    name="apps.records.tasks.dispatch_pending_document_scans",
    ignore_result=True,
    acks_late=True,
)
def dispatch_pending_document_scans() -> int:
    """Reenvia itens pendentes ou falhos, respeitando o limite de tentativas."""

    batch_size = max(int(getattr(settings, "CLINICAL_SCAN_DISPATCH_BATCH_SIZE", 20)), 1)
    max_attempts = max(int(getattr(settings, "CLINICAL_SCAN_MAX_ATTEMPTS", 3)), 1)
    ids = list(
        ClinicalDocument.objects.filter(
            scan_status__in=[
                ClinicalDocument.ScanStatus.PENDING,
                ClinicalDocument.ScanStatus.FAILED,
            ],
            scan_attempts__lt=max_attempts,
            quarantine_file__isnull=False,
        )
        .order_by("created_at")
        .values_list("id", flat=True)[:batch_size]
    )
    published = 0
    for document_id in ids:
        try:
            scan_clinical_document.apply_async(args=[document_id], queue="uploads")
            published += 1
        except Exception as exc:
            logger.error(
                "clinical_document_scan_publish_failed",
                extra={
                    "document_id": document_id,
                    "exception_type": exc.__class__.__name__,
                },
            )
    return published


@shared_task(
    name="apps.records.tasks.recover_stuck_document_scans",
    ignore_result=True,
    acks_late=True,
)
def recover_stuck_document_scans() -> int:
    timeout_minutes = max(int(getattr(settings, "CLINICAL_SCAN_PROCESSING_TIMEOUT_MINUTES", 5)), 1)
    cutoff = timezone.now() - timedelta(minutes=timeout_minutes)
    recovered = 0
    ids = list(
        ClinicalDocument.objects.filter(
            scan_status=ClinicalDocument.ScanStatus.SCANNING,
            scan_started_at__lt=cutoff,
        ).values_list("id", flat=True)[:100]
    )
    for document_id in ids:
        with transaction.atomic():
            document = ClinicalDocument.objects.select_for_update().get(pk=document_id)
            if (
                document.scan_status != ClinicalDocument.ScanStatus.SCANNING
                or not document.scan_started_at
                or document.scan_started_at >= cutoff
            ):
                continue
            document.scan_status = ClinicalDocument.ScanStatus.FAILED
            document.scan_error_code = "worker_timeout"
            document.scanned_at = timezone.now()
            document.save(
                update_fields=[
                    "scan_status",
                    "scan_error_code",
                    "scanned_at",
                    "updated_at",
                ]
            )
            recovered += 1
    return recovered


@shared_task(
    name="apps.records.tasks.cleanup_rejected_clinical_documents",
    ignore_result=True,
    acks_late=True,
)
def cleanup_rejected_clinical_documents() -> int:
    """Remove bytes rejeitados ou falhos após o prazo de retenção técnica."""

    retention_hours = max(int(getattr(settings, "CLINICAL_QUARANTINE_RETENTION_HOURS", 24)), 1)
    max_attempts = max(int(getattr(settings, "CLINICAL_SCAN_MAX_ATTEMPTS", 3)), 1)
    cutoff = timezone.now() - timedelta(hours=retention_hours)
    queryset = ClinicalDocument.objects.filter(quarantine_file__isnull=False).filter(
        Q(scan_status=ClinicalDocument.ScanStatus.INFECTED)
        | Q(
            scan_status=ClinicalDocument.ScanStatus.FAILED,
            scan_attempts__gte=max_attempts,
            updated_at__lt=cutoff,
        )
    )
    removed = 0
    for document_id in list(queryset.values_list("id", flat=True)[:200]):
        with transaction.atomic():
            document = ClinicalDocument.objects.select_for_update().get(pk=document_id)
            if not document.quarantine_file:
                continue
            file_name = document.quarantine_file.name
            storage = document.quarantine_file.storage
            try:
                storage.delete(file_name)
            except Exception as exc:
                logger.warning(
                    "clinical_quarantine_cleanup_failed",
                    extra={
                        "document_id": document_id,
                        "exception_type": exc.__class__.__name__,
                    },
                )
                continue
            document.quarantine_file = None
            document.save(update_fields=["quarantine_file", "updated_at"])
            removed += 1
    return removed


@shared_task(
    bind=True,
    name="apps.records.tasks.generate_clinical_export",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=360,
)
def generate_clinical_export(self, export_id: int) -> None:
    try:
        process_clinical_export(export_id, task_id=str(self.request.id or "celery"))
    except SoftTimeLimitExceeded as exc:
        register_export_failure(export_id, exception=exc, final=True)
        raise
    except Exception as exc:
        final = self.request.retries >= self.max_retries
        countdown = min(30 * (2**self.request.retries), 600)
        register_export_failure(
            export_id,
            exception=exc,
            final=final,
            retry_in_seconds=countdown,
        )
        if final:
            raise
        raise self.retry(exc=exc, countdown=countdown, max_retries=self.max_retries)


@shared_task(name="apps.records.tasks.dispatch_pending_exports", ignore_result=True, acks_late=True)
def dispatch_pending_exports() -> int:
    """Reserva jobs no PostgreSQL e publica somente seus identificadores no Redis."""

    now = timezone.now()
    batch_size = max(int(getattr(settings, "CLINICAL_EXPORT_DISPATCH_BATCH_SIZE", 20)), 1)
    scheduled: list[tuple[int, str]] = []
    with transaction.atomic():
        jobs = list(
            ClinicalExport.objects.select_for_update(skip_locked=True)
            .filter(status=ClinicalExport.Status.PENDING)
            .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
            .order_by("created_at")[:batch_size]
        )
        for job in jobs:
            task_id = celery_uuid()
            job.status = ClinicalExport.Status.PROCESSING
            job.started_at = now
            job.worker_id = task_id
            job.progress = 5
            job.save(update_fields=["status", "started_at", "worker_id", "progress"])
            scheduled.append((job.pk, task_id))

    published = 0
    for export_id, task_id in scheduled:
        try:
            generate_clinical_export.apply_async(args=[export_id], task_id=task_id, queue="exports")
            published += 1
        except Exception as exc:
            register_export_failure(export_id, exception=exc, final=False, retry_in_seconds=30)
    return published


@shared_task(name="apps.records.tasks.recover_stuck_exports", ignore_result=True, acks_late=True)
def recover_stuck_exports() -> dict[str, int]:
    now = timezone.now()
    timeout_minutes = max(int(getattr(settings, "CLINICAL_EXPORT_PROCESSING_TIMEOUT_MINUTES", 15)), 1)
    max_retries = max(int(getattr(settings, "CLINICAL_EXPORT_MAX_RETRIES", 3)), 1)
    cutoff = now - timedelta(minutes=timeout_minutes)
    recovered = failed = 0

    ids = list(
        ClinicalExport.objects.filter(
            status=ClinicalExport.Status.PROCESSING,
            started_at__lt=cutoff,
        ).values_list("id", flat=True)[:100]
    )
    for export_id in ids:
        with transaction.atomic():
            export_obj = ClinicalExport.objects.select_for_update().get(pk=export_id)
            if export_obj.status != ClinicalExport.Status.PROCESSING:
                continue
            export_obj.worker_id = ""
            export_obj.progress = 0
            export_obj.error_code = "WorkerTimeout"
            if export_obj.retries >= max_retries:
                export_obj.status = ClinicalExport.Status.FAILED
                export_obj.completed_at = now
                export_obj.error_message = "Tempo limite de processamento excedido."
                failed += 1
            else:
                export_obj.status = ClinicalExport.Status.PENDING
                export_obj.retries += 1
                export_obj.started_at = None
                export_obj.next_attempt_at = now + timedelta(seconds=min(30 * export_obj.retries, 300))
                export_obj.error_message = "Job recuperado após interrupção do worker."
                recovered += 1
            export_obj.save()
    return {"recovered": recovered, "failed": failed}


@shared_task(name="apps.records.tasks.expire_clinical_exports", ignore_result=True, acks_late=True)
def expire_clinical_exports() -> int:
    now = timezone.now()
    expired = 0
    export_ids = list(
        ClinicalExport.objects.filter(
            status=ClinicalExport.Status.COMPLETED,
            expires_at__lte=now,
        ).values_list("id", flat=True)[:200]
    )
    for export_id in export_ids:
        with transaction.atomic():
            export_obj = ClinicalExport.objects.select_for_update().get(pk=export_id)
            if export_obj.status != ClinicalExport.Status.COMPLETED:
                continue
            if export_obj.file:
                try:
                    export_obj.file.delete(save=False)
                except Exception as exc:
                    logger.warning(
                        "clinical_export_file_cleanup_failed",
                        extra={"export_id": export_id, "exception_type": exc.__class__.__name__},
                    )
                    continue
            export_obj.file = None
            export_obj.status = ClinicalExport.Status.EXPIRED
            export_obj.download_url = ""
            export_obj.metadata = {**(export_obj.metadata or {}), "expired_at": now.isoformat()}
            export_obj.save(update_fields=["file", "status", "download_url", "metadata"])
            expired += 1
    return expired
