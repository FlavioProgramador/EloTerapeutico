from datetime import time, timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.users.models import WorkingHours


@pytest.mark.django_db
def test_lock_expiration_and_reset_are_persisted(therapist_user):
    therapist_user.failed_login_attempts = 4
    therapist_user.locked_until = timezone.now() - timedelta(seconds=1)
    therapist_user.save(update_fields=["failed_login_attempts", "locked_until"])

    assert therapist_user.is_locked() is False

    therapist_user.lock_account(minutes=5)
    assert therapist_user.is_locked() is True

    therapist_user.reset_login_attempts()
    therapist_user.refresh_from_db()
    assert therapist_user.failed_login_attempts == 0
    assert therapist_user.locked_until is None


@pytest.mark.django_db
def test_working_hours_are_unique_per_therapist_and_weekday(therapist_user):
    WorkingHours.objects.create(
        therapist=therapist_user,
        weekday=WorkingHours.Weekday.MONDAY,
        start_time=time(8, 0),
        end_time=time(12, 0),
    )

    with pytest.raises(IntegrityError):
        WorkingHours.objects.create(
            therapist=therapist_user,
            weekday=WorkingHours.Weekday.MONDAY,
            start_time=time(13, 0),
            end_time=time(17, 0),
        )
