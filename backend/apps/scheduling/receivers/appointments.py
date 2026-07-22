from functools import partial

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.scheduling.integrations.communications import (
    synchronize_sent_telemedicine_communications,
)
from apps.scheduling.models import Appointment
from apps.scheduling.services.telemedicine_lifecycle import (
    sync_telemedicine_for_appointment,
)


@receiver(
    pre_save,
    sender=Appointment,
    dispatch_uid="agenda.capture_telemedicine_appointment_state",
)
def capture_telemedicine_appointment_state(
    sender,
    instance: Appointment,
    raw: bool = False,
    **kwargs,
):
    del sender, kwargs
    if raw or not instance.pk:
        instance._telemedicine_previous_state = None
        return
    instance._telemedicine_previous_state = (
        Appointment.objects.filter(pk=instance.pk)
        .values("start_time", "status", "modality")
        .first()
    )


@receiver(
    post_save,
    sender=Appointment,
    dispatch_uid="agenda.sync_telemedicine_for_appointment",
)
def synchronize_telemedicine_room(
    sender,
    instance: Appointment,
    raw: bool = False,
    **kwargs,
):
    del sender, kwargs
    if raw:
        return

    actor = instance.updated_by or instance.created_by or instance.therapist
    room = sync_telemedicine_for_appointment(
        appointment=instance,
        actor=actor,
    )
    previous = getattr(instance, "_telemedicine_previous_state", None)
    if room is None or not previous:
        return

    transaction.on_commit(
        partial(
            synchronize_sent_telemedicine_communications,
            actor=actor,
            room=room,
            previous_start_time=previous["start_time"],
            previous_status=previous["status"],
            previous_modality=previous["modality"],
        )
    )
