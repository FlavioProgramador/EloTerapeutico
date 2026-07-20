from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.communications.models import PublicCommunicationActionToken
from apps.communications.services import (
    cancel_pending_for_source,
    emit_domain_event,
    issue_appointment_action_links,
)
from apps.scheduling.models import Appointment

from .common import capture_previous, has_active_automation


@receiver(pre_save, sender=Appointment)
def capture_appointment_previous_state(sender, instance, **kwargs):
    capture_previous(
        sender,
        instance,
        ("start_time", "end_time", "status", "updated_at"),
        "_communications_previous_state",
    )


@receiver(post_save, sender=Appointment)
def enqueue_appointment_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        created_event = created and has_active_automation(
            instance.therapist,
            "appointment.created",
        )
        reminder_event = has_active_automation(
            instance.therapist,
            "appointment.reminder_due",
        )
        rescheduled = bool(previous and previous["start_time"] != instance.start_time)
        rescheduled_event = rescheduled and has_active_automation(
            instance.therapist,
            "appointment.rescheduled",
        )
        canceled = bool(
            previous
            and previous["status"] != instance.status
            and instance.status == Appointment.Status.CANCELLED
        )
        canceled_event = canceled and has_active_automation(
            instance.therapist,
            "appointment.canceled",
        )
        links_required = created_event or reminder_event or rescheduled_event
        links = (
            issue_appointment_action_links(
                instance.therapist,
                instance.patient,
                instance,
            )
            if links_required
            else {}
        )
        if created:
            if created_event:
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="appointment.created",
                    patient=instance.patient,
                    appointment=instance,
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                    variables=links,
                    event_version=version,
                )
            if reminder_event:
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="appointment.reminder_due",
                    patient=instance.patient,
                    appointment=instance,
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                    variables=links,
                    event_version=version,
                )
            return
        if rescheduled:
            cancel_pending_for_source(
                owner=instance.therapist,
                source_event_prefix="appointment.",
                source_object_type="agenda.Appointment",
                source_object_id=source_id,
            )
            PublicCommunicationActionToken.objects.filter(
                owner=instance.therapist,
                appointment=instance,
                used_at__isnull=True,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
            links = (
                issue_appointment_action_links(
                    instance.therapist,
                    instance.patient,
                    instance,
                )
                if rescheduled_event or reminder_event
                else {}
            )
            if rescheduled_event:
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="appointment.rescheduled",
                    patient=instance.patient,
                    appointment=instance,
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                    variables=links,
                    event_version=version,
                )
            if reminder_event:
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="appointment.reminder_due",
                    patient=instance.patient,
                    appointment=instance,
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                    variables=links,
                    event_version=version,
                )
        if previous and previous["status"] != instance.status:
            if instance.status == Appointment.Status.CANCELLED:
                cancel_pending_for_source(
                    owner=instance.therapist,
                    source_event_prefix="appointment.",
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                )
                PublicCommunicationActionToken.objects.filter(
                    owner=instance.therapist,
                    appointment=instance,
                    used_at__isnull=True,
                    revoked_at__isnull=True,
                ).update(revoked_at=timezone.now())
                if canceled_event:
                    emit_domain_event(
                        owner=instance.therapist,
                        event_type="appointment.canceled",
                        patient=instance.patient,
                        appointment=instance,
                        source_object_type="agenda.Appointment",
                        source_object_id=source_id,
                        variables={},
                        event_version=version,
                    )
            elif instance.status == Appointment.Status.CONFIRMED:
                emit_domain_event(
                    owner=instance.therapist,
                    event_type="appointment.confirmed",
                    patient=instance.patient,
                    appointment=instance,
                    source_object_type="agenda.Appointment",
                    source_object_id=source_id,
                    variables=links,
                    event_version=version,
                )

    transaction.on_commit(dispatch_event)
