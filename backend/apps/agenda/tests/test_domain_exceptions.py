from datetime import date, time
from types import SimpleNamespace

import pytest

from apps.agenda.services import core_services
from apps.core.exceptions import AuthorizationError, DomainIntegrityError


def test_package_boundary_uses_authorization_error():
    appointment = SimpleNamespace(patient_id=1, therapist_id=2)
    package = SimpleNamespace(patient_id=99, therapist_id=2)

    with pytest.raises(AuthorizationError) as error:
        core_services.create_appointment_resources(appointment, package=package)

    assert error.value.status_code == 403
    assert error.value.code == "agenda_package_access_denied"


@pytest.mark.django_db
def test_recurrence_conflict_uses_domain_integrity_error(monkeypatch):
    target_date = date(2026, 7, 20)
    rule = SimpleNamespace(
        timezone_name="America/Sao_Paulo",
        start_time=time(10, 0),
        duration_minutes=50,
        therapist=SimpleNamespace(),
        patient=SimpleNamespace(),
        room=None,
    )
    monkeypatch.setattr(core_services, "recurrence_dates", lambda _rule: [target_date])
    monkeypatch.setattr(
        core_services.Appointment,
        "conflict_details",
        lambda **_kwargs: {"therapist": True, "patient": False, "room": False},
    )

    with pytest.raises(DomainIntegrityError) as error:
        core_services.generate_recurrence_appointments(rule)

    assert error.value.status_code == 409
    assert error.value.code == "agenda_recurrence_conflict"
