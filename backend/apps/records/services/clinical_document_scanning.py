"""Casos de uso do ciclo de quarentena e liberação de documentos clínicos."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.core.files import File
from django.db import transaction
from django.utils import timezone

from apps.records.services.malware_scanning import MalwareScanResult, scan_clinical_file
from apps.records.treatment_models import ClinicalDocument

logger = logging.getLogger(__name__)


class ClinicalDocumentScanStateError(RuntimeError):
    """O documento não está em um estado válido para análise."""


class ClinicalDocumentQuarantineMissing(RuntimeError):
    """O arquivo esperado na quarentena não está disponível."""


@dataclass(frozen=True, slots=True)
class ScanProcessingResult:
    document_id: int
    status: str


def create_quarantined_document(
    *,
    patient,
    uploaded_by,
    uploaded_file,
    original_name: str,
    content_type: str,
    checksum: str,
    validated_data: dict,
) -> ClinicalDocument:
    """Persiste somente na quarentena e agenda a análise após o commit."""

    payload = dict(validated_data)
    payload.pop("file", None)
    with transaction.atomic():
        document = ClinicalDocument.objects.create(
            patient=patient,
            organization=patient.organization,
            uploaded_by=uploaded_by,
            quarantine_file=uploaded_file,
            file=None,
            original_name=original_name,
            content_type=content_type,
            size_bytes=uploaded_file.size,
            checksum=checksum,
            scan_status=ClinicalDocument.ScanStatus.PENDING,
            scan_error_code="",
            **payload,
        )

        def dispatch() -> None:
            try:
                from apps.records.tasks import scan_clinical_document

                scan_clinical_document.delay(document.pk)
            except Exception as exc:  # tarefa periódica recupera o item pendente
                logger.error(
                    "clinical_document_scan_dispatch_failed",
                    extra={
                        "document_id": document.pk,
                        "exception_type": exc.__class__.__name__,
                    },
                )

        transaction.on_commit(dispatch)
    return document


def _reserve_document(document_id: int) -> ClinicalDocument:
    with transaction.atomic():
        document = ClinicalDocument.objects.select_for_update().get(pk=document_id)
        if document.scan_status in {
            ClinicalDocument.ScanStatus.CLEAN,
            ClinicalDocument.ScanStatus.INFECTED,
        }:
            return document
        if not document.quarantine_file:
            document.scan_status = ClinicalDocument.ScanStatus.FAILED
            document.scan_error_code = "quarantine_missing"
            document.scanned_at = timezone.now()
            document.save(
                update_fields=[
                    "scan_status",
                    "scan_error_code",
                    "scanned_at",
                    "updated_at",
                ]
            )
            raise ClinicalDocumentQuarantineMissing("Arquivo de quarentena ausente.")

        document.scan_status = ClinicalDocument.ScanStatus.SCANNING
        document.scan_started_at = timezone.now()
        document.scanned_at = None
        document.scan_error_code = ""
        document.scan_attempts += 1
        document.save(
            update_fields=[
                "scan_status",
                "scan_started_at",
                "scanned_at",
                "scan_error_code",
                "scan_attempts",
                "updated_at",
            ]
        )
        return document


def _mark_failure(document_id: int, code: str) -> None:
    with transaction.atomic():
        document = ClinicalDocument.objects.select_for_update().get(pk=document_id)
        if document.scan_status in {
            ClinicalDocument.ScanStatus.CLEAN,
            ClinicalDocument.ScanStatus.INFECTED,
        }:
            return
        document.scan_status = ClinicalDocument.ScanStatus.FAILED
        document.scan_error_code = code[:64]
        document.scanned_at = timezone.now()
        document.save(
            update_fields=[
                "scan_status",
                "scan_error_code",
                "scanned_at",
                "updated_at",
            ]
        )


def register_document_scan_failure(document_id: int, exception: Exception) -> None:
    error_code = {
        "MalwareScannerUnavailable": "scanner_unavailable",
        "MalwareScannerProtocolError": "scanner_protocol_error",
        "ClinicalDocumentQuarantineMissing": "quarantine_missing",
    }.get(exception.__class__.__name__, "scan_processing_error")
    _mark_failure(document_id, error_code)
    logger.error(
        "clinical_document_scan_failed",
        extra={
            "document_id": document_id,
            "error_code": error_code,
            "exception_type": exception.__class__.__name__,
        },
    )


def _release_clean_document(document_id: int) -> None:
    document = ClinicalDocument.objects.get(pk=document_id)
    if not document.quarantine_file:
        raise ClinicalDocumentQuarantineMissing("Arquivo de quarentena ausente.")

    storage = document.file.storage
    final_name = document.file.field.generate_filename(document, document.original_name)
    try:
        with document.quarantine_file.open("rb") as source:
            saved_name = storage.save(final_name, File(source, name=document.original_name))
    except FileNotFoundError as exc:
        raise ClinicalDocumentQuarantineMissing("Arquivo de quarentena ausente.") from exc

    try:
        with transaction.atomic():
            locked = ClinicalDocument.objects.select_for_update().get(pk=document_id)
            if locked.scan_status != ClinicalDocument.ScanStatus.SCANNING:
                raise ClinicalDocumentScanStateError("Estado alterado durante a análise.")
            locked.file.name = saved_name
            locked.scan_status = ClinicalDocument.ScanStatus.CLEAN
            locked.scan_error_code = ""
            locked.scanned_at = timezone.now()
            locked.save(
                update_fields=[
                    "file",
                    "scan_status",
                    "scan_error_code",
                    "scanned_at",
                    "updated_at",
                ]
            )
    except Exception:
        storage.delete(saved_name)
        raise

    quarantine_name = document.quarantine_file.name
    quarantine_storage = document.quarantine_file.storage
    try:
        quarantine_storage.delete(quarantine_name)
    except Exception as exc:
        logger.warning(
            "clinical_document_quarantine_cleanup_failed",
            extra={
                "document_id": document_id,
                "exception_type": exc.__class__.__name__,
            },
        )
        return
    ClinicalDocument.objects.filter(pk=document_id).update(quarantine_file=None)


def _reject_infected_document(document_id: int, result: MalwareScanResult) -> None:
    with transaction.atomic():
        document = ClinicalDocument.objects.select_for_update().get(pk=document_id)
        if document.scan_status != ClinicalDocument.ScanStatus.SCANNING:
            raise ClinicalDocumentScanStateError("Estado alterado durante a análise.")
        document.scan_status = ClinicalDocument.ScanStatus.INFECTED
        document.scan_error_code = "malware_detected"
        document.scanned_at = timezone.now()
        document.file = None
        document.save(
            update_fields=[
                "file",
                "scan_status",
                "scan_error_code",
                "scanned_at",
                "updated_at",
            ]
        )
        quarantine_name = document.quarantine_file.name if document.quarantine_file else ""
        quarantine_storage = document.quarantine_file.storage if document.quarantine_file else None

    if quarantine_name and quarantine_storage:
        try:
            quarantine_storage.delete(quarantine_name)
        except Exception as exc:
            logger.warning(
                "infected_clinical_document_cleanup_failed",
                extra={
                    "document_id": document_id,
                    "exception_type": exc.__class__.__name__,
                },
            )
            return
        ClinicalDocument.objects.filter(pk=document_id).update(quarantine_file=None)

    logger.warning(
        "clinical_document_rejected_by_scanner",
        extra={
            "document_id": document_id,
            "signature_present": bool(result.signature),
        },
    )


def process_clinical_document_scan(document_id: int) -> ScanProcessingResult:
    """Analisa um item reservado e libera somente resultados limpos."""

    document = _reserve_document(document_id)
    if document.scan_status in {
        ClinicalDocument.ScanStatus.CLEAN,
        ClinicalDocument.ScanStatus.INFECTED,
    }:
        return ScanProcessingResult(document_id=document_id, status=document.scan_status)

    try:
        with document.quarantine_file.open("rb") as stream:
            result = scan_clinical_file(stream)
    except FileNotFoundError as exc:
        raise ClinicalDocumentQuarantineMissing("Arquivo de quarentena ausente.") from exc

    if result.clean:
        _release_clean_document(document_id)
        return ScanProcessingResult(
            document_id=document_id,
            status=ClinicalDocument.ScanStatus.CLEAN,
        )

    _reject_infected_document(document_id, result)
    return ScanProcessingResult(
        document_id=document_id,
        status=ClinicalDocument.ScanStatus.INFECTED,
    )
