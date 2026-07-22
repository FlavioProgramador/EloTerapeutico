from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.scheduling.models import Appointment
from apps.scheduling.services.telemedicine_lifecycle import (
    sync_telemedicine_for_appointment,
)


@receiver(
    post_save,
    sender=Appointment,
    dispatch_uid="agenda.sync_telemedicine_for_appointment",
)
def synchronize_telemedicine_room(sender, instance: Appointment, raw: bool, **kwargs):
    del sender, kwargs
    if raw:
        return
    sync_telemedicine_for_appointment(
        appointment=instance,
        actor=instance.updated_by or instance.created_by,
    )
