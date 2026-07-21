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
from apps.organizations.models import OrganizationMembership


@receiver(post_save, sender=get_user_model())
def bootstrap_user_communications(sender, instance, created, **kwargs):
    if not created:
        return

    def bootstrap():
        membership = (
            OrganizationMembership.objects.filter(
                user=instance,
                status=OrganizationMembership.Status.ACTIVE,
            )
            .select_related("organization")
            .order_by("-is_default", "created_at")
            .first()
        )
        if membership is not None:
            ensure_default_channels(
                instance,
                organization=membership.organization,
            )
            ensure_default_automations(
                instance,
                organization=membership.organization,
            )

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
