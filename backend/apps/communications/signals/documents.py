from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.communications.services import (
    cancel_pending_for_source,
    emit_domain_event,
    issue_document_access_link,
)
from apps.documents.models import GeneratedDocument

from .common import capture_previous, has_active_automation


@receiver(pre_save, sender=GeneratedDocument)
def capture_document_previous_state(sender, instance, **kwargs):
    capture_previous(
        sender,
        instance,
        ("status", "signed_at", "updated_at"),
        "_communications_previous_state",
    )


@receiver(post_save, sender=GeneratedDocument)
def enqueue_document_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        became_available = (
            instance.status == GeneratedDocument.Status.COMPLETED
            and (
                created
                or not previous
                or previous["status"] != GeneratedDocument.Status.COMPLETED
            )
        )
        if became_available and has_active_automation(
            instance.owner,
            "document.available",
        ):
            document_link = issue_document_access_link(
                instance.owner,
                instance.patient,
                instance,
            )
            emit_domain_event(
                owner=instance.owner,
                event_type="document.available",
                patient=instance.patient,
                document=instance,
                source_object_type="documents.GeneratedDocument",
                source_object_id=source_id,
                variables={
                    "document_name": instance.title,
                    "document_link": document_link,
                },
                event_version=version,
            )
        if (
            previous
            and previous["signed_at"] is None
            and instance.signed_at is not None
        ):
            cancel_pending_for_source(
                owner=instance.owner,
                source_event_prefix="document.",
                source_object_type="documents.GeneratedDocument",
                source_object_id=source_id,
            )
            emit_domain_event(
                owner=instance.owner,
                event_type="document.signed",
                patient=instance.patient,
                document=instance,
                source_object_type="documents.GeneratedDocument",
                source_object_id=source_id,
                variables={"document_name": instance.title},
                event_version=version,
            )

    transaction.on_commit(dispatch_event)
