"""Testes de minimização e integridade da trilha de auditoria."""

from datetime import date

import pytest
from django.test import RequestFactory, override_settings

from apps.audit.models import AuditLog
from apps.patients.models import Patient
from apps.users.models import User
from core.audit import log_access


@pytest.mark.django_db
def test_default_object_repr_does_not_use_sensitive_model_string():
    therapist = User.objects.create_user(
        email="audit-owner@teste.com",
        full_name="Audit Owner",
        password="".join(["Test", "Pass", "2026!", "_audit"]),
    )
    patient = Patient.objects.create(
        full_name="Nome Pessoal Que Não Deve Ir Ao Log",
        cpf="52998224725",
        birth_date=date(1990, 1, 1),
        therapist=therapist,
    )
    request = RequestFactory().get("/api/v1/patients/", REMOTE_ADDR="127.0.0.1")
    request.user = therapist

    log_access(request, AuditLog.Action.VIEW, obj=patient)

    entry = AuditLog.objects.get()
    assert entry.object_repr == f"patients.Patient#{patient.pk}"
    assert patient.full_name not in entry.object_repr
    assert patient.cpf not in entry.object_repr


@pytest.mark.django_db
def test_audit_ignores_untrusted_forwarded_ip_and_normalizes_headers():
    user = User.objects.create_user(
        email="audit-ip@teste.com",
        full_name="Audit IP",
        password="".join(["Test", "Pass", "2026!", "_ip"]),
    )
    request = RequestFactory().get(
        "/api/v1/test/",
        REMOTE_ADDR="127.0.0.1",
        HTTP_X_FORWARDED_FOR="203.0.113.99",
        HTTP_USER_AGENT="Browser\r\nInjected-Header: value",
    )
    request.user = user

    log_access(
        request,
        AuditLog.Action.VIEW,
        obj_repr="Descrição\ncontrolada",
    )

    entry = AuditLog.objects.get()
    assert str(entry.ip_address) == "127.0.0.1"
    assert entry.user_agent == "Browser Injected-Header: value"
    assert entry.object_repr == "Descrição controlada"


@pytest.mark.django_db
@override_settings(TRUST_PROXY_CLIENT_IP_HEADERS=True)
def test_audit_accepts_valid_azure_client_ip_when_proxy_headers_are_trusted():
    user = User.objects.create_user(
        email="audit-proxy@teste.com",
        full_name="Audit Proxy",
        password="".join(["Test", "Pass", "2026!", "_proxy"]),
    )
    request = RequestFactory().get(
        "/api/v1/test/",
        REMOTE_ADDR="10.0.0.10",
        HTTP_X_AZURE_CLIENTIP="203.0.113.42",
    )
    request.user = user

    log_access(request, AuditLog.Action.VIEW, obj_repr="Acesso via proxy")

    assert str(AuditLog.objects.get().ip_address) == "203.0.113.42"
