"""Regras de acesso do domínio documental."""

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.patients.models import Patient


def ensure_patient_access(*, actor, patient: Patient) -> None:
    if actor.is_secretary:
        raise DocumentDomainError("Secretárias não possuem acesso a documentos clínicos.")
    if patient.therapist_id != actor.id:
        raise DocumentDomainError("Paciente não autorizado para este profissional.")


def ensure_template_access(*, actor, template: DocumentTemplate) -> None:
    if template.status != DocumentTemplate.Status.ACTIVE:
        raise DocumentDomainError("O template selecionado não está ativo.")
    if template.is_library_template:
        raise DocumentDomainError("Importe o template da biblioteca antes de utilizá-lo.")
    if template.owner_id != actor.id:
        raise DocumentDomainError("Template não autorizado.")


def ensure_document_access(*, actor, document: GeneratedDocument) -> None:
    if document.owner_id != actor.id:
        raise DocumentDomainError("Documento não autorizado.")
