"""Selectors de usuários relevantes para scheduling."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


def get_accessible_therapist(*, actor, therapist_id=None):
    """Resolve o profissional respeitando o papel do ator."""

    if actor.is_therapist or not therapist_id:
        return actor
    if actor.is_admin_role or actor.is_secretary:
        return get_object_or_404(
            get_user_model().objects.filter(role="therapist"),
            pk=therapist_id,
        )
    return actor


__all__ = ["get_accessible_therapist"]
