"""Consultas de leitura para documentos gerados."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import GeneratedDocument


def generated_documents_for_owner(*, owner) -> QuerySet[GeneratedDocument]:
    return GeneratedDocument.objects.filter(owner=owner).select_related(
        "patient",
        "professional",
        "template",
    )


def find_by_idempotency_key(*, owner, idempotency_key: str) -> GeneratedDocument | None:
    return GeneratedDocument.objects.filter(
        owner=owner,
        idempotency_key=idempotency_key,
    ).first()
