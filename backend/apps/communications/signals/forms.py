from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.communications.models import PublicCommunicationActionToken
from apps.communications.services import (
    cancel_pending_for_source,
    emit_domain_event,
    issue_form_access_link,
)
from apps.forms.models import FormSubmission

from .common import capture_previous, has_active_automation


@receiver(pre_save, sender=FormSubmission)
def capture_form_submission_previous_state(sender, instance, **kwargs):
    capture_previous(
        sender,
        instance,
        ("status", "updated_at"),
        "_communications_previous_state",
    )


@receiver(post_save, sender=FormSubmission)
def enqueue_form_submission_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)
    if instance.patient_id is None:
        return

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        if created and instance.status == FormSubmission.Status.DRAFT:
            if not has_active_automation(instance.owner, "form.assigned"):
                return
            form_link = issue_form_access_link(
                instance.owner,
                instance.patient,
                instance,
            )
            emit_domain_event(
                owner=instance.owner,
                event_type="form.assigned",
                patient=instance.patient,
                form_submission=instance,
                source_object_type="forms.FormSubmission",
                source_object_id=source_id,
                variables={
                    "form_name": instance.form.name,
                    "form_link": form_link,
                },
                event_version=version,
            )
            return
        if (
            previous
            and previous["status"] != instance.status
            and instance.status == FormSubmission.Status.SUBMITTED
        ):
            cancel_pending_for_source(
                owner=instance.owner,
                source_event_prefix="form.",
                source_object_type="forms.FormSubmission",
                source_object_id=source_id,
            )
            PublicCommunicationActionToken.objects.filter(
                owner=instance.owner,
                form_submission=instance,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
            emit_domain_event(
                owner=instance.owner,
                event_type="form.submitted",
                patient=instance.patient,
                form_submission=instance,
                source_object_type="forms.FormSubmission",
                source_object_id=source_id,
                variables={"form_name": instance.form.name},
                event_version=version,
            )

    transaction.on_commit(dispatch_event)
