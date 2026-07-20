from datetime import date

import pytest
from django.db import transaction
from django.test import RequestFactory, override_settings

from apps.audit.exceptions import AuditWriteError, InvalidAuditActionError
from apps.audit.models import AuditLog
from apps.audit.services import (
    extract_request_context,
    record_audit_event,
    safe_resource_repr,
    sanitize_metadata,
)
from apps.audit.types import AuditWritePolicy
from apps.patients.models import Patient
from apps.users.models import User


def _user(email: str) -> User:
    return User.objects.create_user(
        email=email,
        full_name="Audit User",
        password="TestPass2026!_audit",
    )


@pytest.mark.django_db
def test_record_audit_event_minimizes_resource_representation():
    therapist = _user("audit-owner@teste.com")
    patient = Patient.objects.create(
        full_name="Nome sensível",
        cpf="52998224725",
        birth_date=date(1990, 1, 1),
        therapist=therapist,
    )
    request = RequestFactory().get("/patients/", REMOTE_ADDR="127.0.0.1")
    request.user = therapist

    result = record_audit_event(
        action=AuditLog.Action.VIEW,
        request=request,
        resource=patient,
        on_commit=False,
    )

    assert result.audit_log.object_repr == f"patients.Patient#{patient.pk}"
    assert patient.full_name not in result.audit_log.object_repr
    assert patient.cpf not in result.audit_log.object_repr


@pytest.mark.django_db(transaction=True)
def test_mutation_event_is_created_only_after_commit():
    user = _user("audit-commit@teste.com")
    with transaction.atomic():
        result = record_audit_event(
            action=AuditLog.Action.UPDATE,
            actor=user,
            resource=user,
            on_commit=True,
        )
        assert result.scheduled is True
        assert AuditLog.objects.count() == 0
    assert AuditLog.objects.count() == 1


@pytest.mark.django_db
def test_invalid_action_is_rejected():
    with pytest.raises(InvalidAuditActionError):
        record_audit_event(action="INVALID", on_commit=False)


def test_sensitive_metadata_is_removed():
    metadata = sanitize_metadata(
        {
            "status": "completed",
            "token": "secret-token",
            "nested": {"password": "hidden", "count": 2},
        }
    )
    assert metadata == {"status": "completed", "nested": {"count": 2}}


def test_safe_resource_repr_does_not_call_str():
    class Resource:
        pk = 10

        class _meta:
            label = "records.Evolution"

        def __str__(self):
            raise AssertionError("__str__ não deve ser chamado")

    assert safe_resource_repr(Resource()) == "records.Evolution#10"


@pytest.mark.django_db
def test_fail_open_policy_does_not_raise(monkeypatch):
    def fail_create(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(AuditLog.objects, "create", fail_create)
    result = record_audit_event(
        action=AuditLog.Action.VIEW,
        on_commit=False,
    )
    assert result.audit_log is None


@pytest.mark.django_db
def test_fail_closed_policy_raises_sanitized_error(monkeypatch):
    def fail_create(**kwargs):
        raise RuntimeError("database unavailable with sensitive text")

    monkeypatch.setattr(AuditLog.objects, "create", fail_create)
    with pytest.raises(AuditWriteError, match="evento obrigatório"):
        record_audit_event(
            action=AuditLog.Action.ANONYMIZE,
            on_commit=False,
            policy=AuditWritePolicy(
                fail_closed_for=frozenset({AuditLog.Action.ANONYMIZE}),
            ),
        )


def test_untrusted_forwarded_ip_is_ignored():
    request = RequestFactory().get(
        "/test/",
        REMOTE_ADDR="127.0.0.1",
        HTTP_X_FORWARDED_FOR="203.0.113.99",
        HTTP_USER_AGENT="Browser\r\nInjected: value",
    )
    context = extract_request_context(request)
    assert context.ip_address == "127.0.0.1"
    assert context.user_agent == "Browser Injected: value"


@override_settings(AUDIT_TRUSTED_PROXY_HOPS=1)
def test_configured_proxy_hop_is_used():
    request = RequestFactory().get(
        "/test/",
        REMOTE_ADDR="10.0.0.10",
        HTTP_X_FORWARDED_FOR="203.0.113.42",
        HTTP_X_REQUEST_ID="request-123",
    )
    context = extract_request_context(request)
    assert context.ip_address == "203.0.113.42"
    assert context.request_id == "request-123"
