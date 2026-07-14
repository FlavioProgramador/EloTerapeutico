"""Sequenciamento transacional de documentos."""

from django.utils import timezone

from apps.documents.models import DocumentSequence


def reserve_document_number(*, owner) -> str:
    year = timezone.localdate().year
    sequence, _ = DocumentSequence.objects.select_for_update().get_or_create(
        owner=owner,
        year=year,
        defaults={"last_value": 0},
    )
    sequence.last_value += 1
    sequence.save(update_fields=["last_value", "updated_at"])
    return f"DOC-{year}-{sequence.last_value:06d}"
