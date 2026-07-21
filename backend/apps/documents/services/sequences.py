"""Sequenciamento transacional de documentos."""

from django.db import transaction
from django.utils import timezone

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentSequence
from apps.organizations.models import OrganizationMembership


def _resolve_organization(*, owner, organization=None):
    if organization is not None:
        return organization
    memberships = OrganizationMembership.objects.filter(
        user=owner,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    membership = memberships.filter(is_default=True).first()
    if membership is None:
        first_two = list(memberships[:2])
        membership = first_two[0] if len(first_two) == 1 else None
    if membership is None:
        raise DocumentDomainError("Selecione uma organização para numerar o documento.")
    return membership.organization


@transaction.atomic
def reserve_document_number(*, owner, organization=None) -> str:
    """Reserva o próximo número anual da organização com bloqueio pessimista."""

    organization = _resolve_organization(owner=owner, organization=organization)
    year = timezone.localdate().year
    sequence, _ = DocumentSequence.objects.select_for_update().get_or_create(
        organization=organization,
        year=year,
        defaults={"owner": owner, "last_value": 0},
    )
    if sequence.owner_id != owner.pk:
        sequence.owner = owner
    sequence.last_value += 1
    sequence.save(update_fields=["owner", "last_value", "updated_at"])
    return f"DOC-{year}-{sequence.last_value:06d}"
