from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils import timezone
from rest_framework.exceptions import MethodNotAllowed

from apps.core.api.pagination import StandardResultsPagination
from apps.core.exceptions import custom_exception_handler
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.finances.models import FinancialTransaction
from apps.finances.selectors import transactions_accessible_to
from apps.finances.services import register_payment
from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.scheduling.models import Appointment


def test_exception_handler_wraps_method_not_allowed():
    response = custom_exception_handler(MethodNotAllowed("TRACE"), {})

    assert response.status_code == 405
    assert response.data["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert response.data["error"]["details"]["detail"]


def test_exception_handler_handles_django_validation_error():
    response = custom_exception_handler(ValidationError("Campo inválido."), {})

    assert response.status_code == 400
    assert response.data["error"]["code"] == "VALIDATION_ERROR"
    assert "Campo inválido" in response.data["error"]["message"]


def test_exception_handler_handles_permission_and_not_found():
    denied = custom_exception_handler(PermissionDenied(), {})
    missing = custom_exception_handler(Http404(), {})

    assert denied.status_code == 403
    assert denied.data["error"]["code"] == "FORBIDDEN"
    assert missing.status_code == 404
    assert missing.data["error"]["code"] == "NOT_FOUND"


def test_pagination_schema_exposes_metadata_contract():
    schema = StandardResultsPagination().get_paginated_response_schema({"type": "array", "items": {"type": "object"}})

    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"pagination", "results"}
    assert set(schema["properties"]["pagination"]["properties"]) == {
        "count",
        "total_pages",
        "current_page",
        "next",
        "previous",
    }


@pytest.mark.django_db
def test_patient_validation_consent_and_soft_delete(therapist_user):
    patient = Patient.objects.create(
        therapist=therapist_user,
        full_name="Paciente Fictício",
        social_name="Nome Social",
        consent_terms_accepted=True,
    )

    assert patient.display_name == "Nome Social"
    assert patient.consent_at is not None

    patient.soft_delete()
    archived = Patient.all_objects.get(pk=patient.pk)
    assert archived.is_active is False
    assert archived.status == Patient.Status.ARCHIVED
    assert Patient.objects.filter(pk=patient.pk).exists() is False

    archived.restore()
    archived.refresh_from_db()
    assert archived.is_active is True
    assert archived.status == Patient.Status.ACTIVE
    assert archived.deleted_at is None


@pytest.mark.django_db
def test_minor_and_insurance_patient_rules(therapist_user):
    minor = Patient(
        therapist=therapist_user,
        full_name="Paciente Menor Fictício",
        birth_date=date.today() - timedelta(days=3650),
    )
    with pytest.raises(ValidationError) as minor_error:
        minor.full_clean()
    assert "guardian_name" in minor_error.value.message_dict

    insured = Patient(
        therapist=therapist_user,
        full_name="Paciente Convênio Fictício",
        payer_type=Patient.PayerType.INSURANCE,
    )
    with pytest.raises(ValidationError) as insurance_error:
        insured.full_clean()
    assert "insurance_name" in insurance_error.value.message_dict


@pytest.mark.django_db
def test_appointment_duration_and_invalid_boundaries(therapist_user):
    patient = Patient.objects.create(
        therapist=therapist_user,
        full_name="Paciente Agenda Fictício",
    )
    start = timezone.now() + timedelta(days=1)
    appointment = Appointment.objects.create(
        therapist=therapist_user,
        patient=patient,
        start_time=start,
        end_time=start + timedelta(minutes=75),
        session_value=Decimal("120.00"),
    )

    assert appointment.duration_minutes == 75
    assert appointment.duration_display == "75 min"

    invalid = Appointment(
        therapist=therapist_user,
        patient=patient,
        start_time=start,
        end_time=start,
        session_value=Decimal("-1.00"),
    )
    with pytest.raises(ValidationError) as error:
        invalid.full_clean()
    assert "end_time" in error.value.message_dict
    assert "__all__" in error.value.message_dict


@pytest.mark.django_db
def test_evolution_lock_prevents_future_edits(therapist_user):
    patient = Patient.objects.create(
        therapist=therapist_user,
        full_name="Paciente Prontuário Fictício",
    )
    evolution = Evolution.objects.create(
        patient=patient,
        content="Conteúdo clínico fictício para teste automatizado.",
        session_date=date.today(),
        created_by=therapist_user,
    )

    assert evolution.can_be_edited() is True
    evolution.lock()
    evolution.refresh_from_db()
    assert evolution.is_locked is True
    assert evolution.locked_at is not None
    assert evolution.can_be_edited() is False


@pytest.mark.django_db
def test_financial_partial_payment_and_tenant_scope(therapist_user, admin_user):
    own = FinancialTransaction.objects.create(
        therapist=therapist_user,
        amount=Decimal("100.00"),
        due_date=date.today(),
    )
    other = FinancialTransaction.objects.create(
        therapist=admin_user,
        amount=Decimal("50.00"),
        due_date=date.today(),
    )

    register_payment(financial_transaction=own, payment_method="pix", amount=Decimal("40.00"))
    own.refresh_from_db()
    assert own.payment_status == FinancialTransaction.PaymentStatus.PARTIAL
    assert own.outstanding_amount == Decimal("60.00")

    register_payment(financial_transaction=own, payment_method="pix")
    own.refresh_from_db()
    assert own.payment_status == FinancialTransaction.PaymentStatus.PAID
    assert own.outstanding_amount == Decimal("0.00")

    therapist_ids = set(transactions_accessible_to(therapist_user).values_list("id", flat=True))
    assert own.id in therapist_ids
    assert other.id not in therapist_ids
    assert transactions_accessible_to(admin_user).filter(id__in=[own.id, other.id]).count() == 2


@pytest.mark.django_db
def test_document_template_archive_and_hash(therapist_user):
    template = DocumentTemplate.objects.create(
        owner=therapist_user,
        name="Modelo Fictício",
        category="Geral",
        content="Conteúdo fictício para teste.",
        created_by=therapist_user,
    )

    assert template.status == DocumentTemplate.Status.ACTIVE
    template.archive()
    template.refresh_from_db()
    assert template.status == DocumentTemplate.Status.ARCHIVED
    assert template.archived_at is not None

    assert GeneratedDocument.calculate_hash(b"conteudo") == GeneratedDocument.calculate_hash(b"conteudo")
    assert GeneratedDocument.calculate_hash(b"conteudo") != GeneratedDocument.calculate_hash(b"outro")
