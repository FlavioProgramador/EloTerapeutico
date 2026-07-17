from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.communications.models import NotificationPreference
from apps.communications.services import (
    ensure_default_automations,
    ensure_default_channels,
)


@receiver(post_save, sender=get_user_model())
def bootstrap_user_communications(sender, instance, created, **kwargs):
    if not created:
        return

    def bootstrap():
        ensure_default_channels(instance)
        ensure_default_automations(instance)
        NotificationPreference.objects.get_or_create(
            user=instance,
            defaults={
                "timezone": getattr(
                    instance,
                    "timezone",
                    "America/Sao_Paulo",
                )
            },
        )
        from apps.users.models import PracticeSettings

        PracticeSettings.objects.get_or_create(
            user=instance,
            defaults={
                "trade_name": instance.clinic_name,
                "phone": instance.phone,
                "email": instance.email,
                "address": instance.professional_address,
                "timezone": getattr(
                    instance,
                    "timezone",
                    "America/Sao_Paulo",
                ),
            },
        )

    transaction.on_commit(bootstrap)
