from __future__ import annotations

from apps.communications.selectors import active_automations_for_event


def capture_previous(sender, instance, fields: tuple[str, ...], attribute: str) -> None:
    if not instance.pk:
        setattr(instance, attribute, None)
        return
    previous = sender.objects.filter(pk=instance.pk).values(*fields).first()
    setattr(instance, attribute, previous)


def has_active_automation(owner, event_type: str) -> bool:
    return active_automations_for_event(owner, event_type).exists()
