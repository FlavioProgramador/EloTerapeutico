"""Sequenciamento transacional de documentos."""

from django.db import transaction
from django.utils import timezone

from apps.documents.models import DocumentSequence


@transaction.atomic
def reserve_document_number(*, organization, owner) -> str:
    """Reserva o próximo número anual da organização com bloqueio pessimista."""

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
