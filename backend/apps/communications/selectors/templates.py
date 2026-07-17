from __future__ import annotations

from django.db.models import Q

from apps.communications.models import CommunicationTemplate


def templates_for_user(user):
    return CommunicationTemplate.objects.filter(
        Q(owner=user) | Q(owner__isnull=True, is_system_template=True),
        is_archived=False,
    ).order_by("name")
