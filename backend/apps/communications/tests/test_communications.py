from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan, Subscription
from apps.forms.models import FormField, FormSubmission, TherapeuticForm
from apps.patients.models import Patient
from apps.users.models import User

from ..models import Communication, CommunicationAttempt, CommunicationPlanEntitlement, CommunicationPreference, InAppNotification, PublicCommunicationActionToken
from ..providers import PROVIDERS, CommunicationProvider, ProviderResult, RetryableProviderError
from ..services import CommunicationLimitExceeded, create_communication, ensure_default_channels, issue_form_access_link, process_due_communications
from ..validators import validate_template_text


@pytest.fixture
def therapist(db):
    return User.objects.create_user(email="communications.therapist@example.test", password="SenhaForte123!", full_name="Terapeuta Comunicações", role=User.Role.THERAPIST, phone="21999998888", onboarding_completed=True)


@pytest.fixture
def other_therapist(db):
    return User.objects.create_user(email="communications.other@example.test", password="SenhaForte123!", full_name="Outro Terapeuta", role=User.Role.THERAPIST, onboarding_completed=True)


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(therapist=therapist, full_name="Paciente Comunicações", email="patient@example.test", phone="21988887777", whatsapp="21988887777", status=Patient.Status.ACTIVE, is_active=True, consent_terms_accepted=True, consent_at=timezone.now())


@pytest.fixture
def authenticated_client(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    return client


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_template_rejects_clinical_variable():
    with pytest.raises(ValidationError):
        validate_template_text("Resumo", "Diagnóstico: {{diagnosis}}")


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_idempotency_returns_same_communication(therapist):
    ensure_default_channels(therapist)
    first = create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Aviso", body="Conteúdo administrativo", idempotency_key="test:idempotency")
    second = create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Aviso duplicado", body="Não deve substituir o snapshot", idempotency_key="test:idempotency")
    assert first.pk == second.pk
    assert Communication.objects.filter(owner=therapist).count() == 1


@pytest.mark.django_db(transaction=True)
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_internal_notification_is_persisted_and_delivered(therapist):
    ensure_default_channels(therapist)
    communication = create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Nova ação", body="Abra o recurso relacionado.", idempotency_key="test:in-app", metadata={"internal_url": "/dashboard/agenda"})
    result = process_due_communications()
    communication.refresh_from_db()
    assert result["processed"] == 1
    assert communication.status == Communication.Status.DELIVERED
    notification = InAppNotification.objects.get(communication=communication)
    assert notification.recipient == therapist
    assert notification.internal_url == "/dashboard/agenda"


@pytest.mark.django_db(transaction=True)
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_email_provider_uses_configured_backend(therapist, patient):
    ensure_default_channels(therapist)
    communication = create_communication(owner=therapist, created_by=therapist, patient=patient, channel=Communication.Channel.EMAIL, category=Communication.Category.PATIENT_MESSAGE, subject="Informação administrativa", body="Mensagem sem conteúdo clínico.", idempotency_key="test:email")
    process_due_communications()
    communication.refresh_from_db()
    assert communication.status == Communication.Status.SENT
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [patient.email]


@pytest.mark.django_db(transaction=True)
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_whatsapp_manual_requires_open_and_confirmation(therapist, patient):
    ensure_default_channels(therapist)
    communication = create_communication(owner=therapist, created_by=therapist, patient=patient, channel=Communication.Channel.WHATSAPP_MANUAL, category=Communication.Category.PATIENT_MESSAGE, body="Mensagem administrativa", idempotency_key="test:whatsapp-manual")
    process_due_communications()
    communication.refresh_from_db()
    assert communication.status == Communication.Status.DRAFT
    assert communication.metadata["manual_url"].startswith("https://wa.me/")
    assert communication.sent_at is None


class AlwaysRetryProvider(CommunicationProvider):
    channel = Communication.Channel.EMAIL
    name = "fake_retry"

    def validate_configuration(self, owner=None) -> None:
        return None

    def send(self, communication, recipient) -> ProviderResult:
        raise RetryableProviderError("temporário")


@pytest.mark.django_db(transaction=True)
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False, COMMUNICATIONS_MAX_ATTEMPTS=5)
def test_retryable_failure_persists_backoff(monkeypatch, therapist, patient):
    ensure_default_channels(therapist)
    monkeypatch.setitem(PROVIDERS, Communication.Channel.EMAIL, AlwaysRetryProvider())
    communication = create_communication(owner=therapist, created_by=therapist, patient=patient, channel=Communication.Channel.EMAIL, category=Communication.Category.PATIENT_MESSAGE, subject="Teste", body="Teste", idempotency_key="test:retry")
    process_due_communications()
    communication.refresh_from_db()
    attempt = CommunicationAttempt.objects.get(communication=communication)
    assert communication.status == Communication.Status.QUEUED
    assert communication.next_retry_at is not None
    assert attempt.status == CommunicationAttempt.Status.RETRYABLE_FAILURE
    assert attempt.next_retry_at == communication.next_retry_at


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_api_isolates_communications_by_owner(authenticated_client, therapist, other_therapist):
    ensure_default_channels(therapist)
    ensure_default_channels(other_therapist)
    own = create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Própria", body="Própria", idempotency_key="test:own", draft=True)
    create_communication(owner=other_therapist, created_by=other_therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Outro tenant", body="Outro tenant", idempotency_key="test:other", draft=True)
    response = authenticated_client.get("/api/v1/communications/")
    assert response.status_code == 200
    assert [item["public_id"] for item in response.data["results"]] == [str(own.public_id)]


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_public_form_token_stores_only_hash_and_is_single_use(therapist, patient):
    form = TherapeuticForm.objects.create(owner=therapist, name="Cadastro administrativo", description="Dados necessários para o atendimento.", created_by=therapist, updated_by=therapist)
    field = FormField.objects.create(form=form, type="short_text", label="Como prefere ser chamado?", required=True, order=1)
    submission = FormSubmission.objects.create(owner=therapist, patient=patient, form=form)
    link = issue_form_access_link(therapist, patient, submission)
    raw_token = link.rsplit("/", 1)[-1]
    token = PublicCommunicationActionToken.objects.get(form_submission=submission)
    assert raw_token not in token.token_hash
    client = APIClient()
    preview = client.get(f"/api/v1/public/communications/actions/{raw_token}/")
    assert preview.status_code == 200
    assert preview.data["form"]["fields"][0]["id"] == field.pk
    response = client.post(f"/api/v1/public/communications/actions/{raw_token}/form-submit/", {"answers": {str(field.pk): "Nome social"}}, format="json")
    assert response.status_code == 200
    submission.refresh_from_db()
    token.refresh_from_db()
    assert submission.status == FormSubmission.Status.SUBMITTED
    assert token.used_at is not None
    assert client.get(f"/api/v1/public/communications/actions/{raw_token}/").status_code == 404


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=True)
def test_monthly_plan_limit_is_enforced(therapist):
    plan = Plan.objects.create(name="Plano limitado", slug="communications-limited", description="", price=Decimal("10.00"), currency="BRL")
    Subscription.objects.create(user=therapist, plan=plan, status=Subscription.Status.ACTIVE, started_at=timezone.now(), access_starts_at=timezone.now() - timedelta(days=1), access_ends_at=timezone.now() + timedelta(days=30))
    CommunicationPlanEntitlement.objects.update_or_create(plan=plan, defaults={"communications_enabled": True, "max_communications_per_month": 1, "max_email_communications_per_month": 1})
    ensure_default_channels(therapist)
    create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Primeira", body="Primeira", idempotency_key="test:limit:first")
    with pytest.raises(CommunicationLimitExceeded):
        create_communication(owner=therapist, created_by=therapist, channel=Communication.Channel.IN_APP, category=Communication.Category.SYSTEM_NOTIFICATION, subject="Segunda", body="Segunda", idempotency_key="test:limit:second")


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_preference_is_unique_per_patient(therapist, patient):
    first, _ = CommunicationPreference.objects.get_or_create(owner=therapist, patient=patient)
    second, created = CommunicationPreference.objects.get_or_create(owner=therapist, patient=patient)
    assert created is False
    assert first.pk == second.pk
