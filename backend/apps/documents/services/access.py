"""Regras de acesso do domínio documental."""

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability
from apps.patients.models import Patient
from apps.patients.services.access_control import can_access_patient


def _membership(*, actor, organization):
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()


def ensure_patient_access(*, actor, patient: Patient) -> None:
    membership = _membership(actor=actor, organization=patient.organization)
    if not has_capability(membership, "documents.view"):
        raise DocumentDomainError("Você não possui acesso documental nesta organização.")
    if not can_access_patient(actor, patient, membership=membership, allow_secretary=False):
        raise DocumentDomainError("Paciente não autorizado nesta organização.")


def ensure_template_access(*, actor, template: DocumentTemplate, organization=None) -> None:
    if template.status != DocumentTemplate.Status.ACTIVE:
        raise DocumentDomainError("O template selecionado não está ativo.")
    if template.is_library_template:
        raise DocumentDomainError("Importe o template da biblioteca antes de utilizá-lo.")
    organization = organization or template.organization
    if template.organization_id != getattr(organization, "pk", organization):
        raise DocumentDomainError("Template pertence a outra organização.")
    membership = _membership(actor=actor, organization=organization)
    if not has_capability(membership, "documents.view"):
        raise DocumentDomainError("Template não autorizado.")


def ensure_document_access(*, actor, document: GeneratedDocument) -> None:
    membership = _membership(actor=actor, organization=document.organization)
    if not has_capability(membership, "documents.view"):
        raise DocumentDomainError("Documento não autorizado.")
    if (
        membership.role == OrganizationMembership.Role.THERAPIST
        and document.professional_id != actor.id
    ):
        raise DocumentDomainError("Documento pertence a outro profissional.")
