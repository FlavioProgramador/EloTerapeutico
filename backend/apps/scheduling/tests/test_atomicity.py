from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.finances.models import FinancialTransaction
from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.api.v1.serializers import (
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
)
from apps.scheduling.api.v1.views.appointments import AppointmentViewSet
from apps.scheduling.models import Appointment
from apps.users.models import User


@pytest.fixture
def atomic_therapist(db):
    return User.objects.create_user(
        email="agenda-atomicidade@teste.com",
        full_name="Terapeuta Atomicidade",
        role=User.Role.THERAPIST,
        crp_number="06/111111",
    )


@pytest.fixture
def atomic_patient(db, atomic_therapist):
    return Patient.objects.create(
        full_name="Paciente Atomicidade",
        cpf="111.222.333-44",
        birth_date=date(1990, 1, 1),
        gender="M",
        email="paciente-atomicidade@teste.com",
        phone="21999999999",
        therapist=atomic_therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def atomic_request(atomic_therapist, atomic_patient):
    request = APIRequestFactory().post(
        "/api/v1/scheduling/appointments/",
        {},
        format="json",
    )
    request.user = atomic_therapist
    request.organization = atomic_patient.organization
    request.organization_membership = OrganizationMembership.objects.get(
        organization=atomic_patient.organization,
        user=atomic_therapist,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return request


@pytest.mark.django_db
def test_appointment_creation_rolls_back_when_derived_resource_fails(
    atomic_therapist,
    atomic_patient,
    atomic_request,
):
    start = timezone.now() + timedelta(days=2)
    serializer = AppointmentCreateSerializer(
        data={
            "patient": atomic_patient.pk,
            "therapist": atomic_therapist.pk,
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(minutes=50)).isoformat(),
            "session_value": "150.00",
            "modality": Appointment.Modality.IN_PERSON,
            "appointment_type": Appointment.AppointmentType.PSYCHOTHERAPY,
        },
        context={"request": atomic_request},
    )
    serializer.is_valid(raise_exception=True)
    with patch(
        "apps.scheduling.services.appointments.create_appointment_resources",
        side_effect=RuntimeError("falha simulada"),
    ):
        with pytest.raises(RuntimeError):
            serializer.save()
    assert Appointment.objects.count() == 0


@pytest.mark.django_db
def test_status_and_financial_entry_roll_back_together(
    atomic_therapist,
    atomic_patient,
    atomic_request,
):
    start = timezone.now() + timedelta(days=1)
    appointment = Appointment.objects.create(
        patient=atomic_patient,
        therapist=atomic_therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value="150.00",
        status=Appointment.Status.SCHEDULED,
    )
    serializer = AppointmentStatusUpdateSerializer(
        appointment,
        data={"status": Appointment.Status.CONFIRMED},
        partial=True,
        context={"request": atomic_request},
    )
    serializer.is_valid(raise_exception=True)
    view = AppointmentViewSet()
    view.request = atomic_request
    with patch(
        "apps.scheduling.services.appointments.create_appointment_transaction",
        side_effect=RuntimeError("falha financeira simulada"),
    ):
        with pytest.raises(RuntimeError):
            view._save_status(serializer, Appointment.Status.CONFIRMED)
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Status.SCHEDULED
    assert not FinancialTransaction.objects.filter(appointment=appointment).exists()


@pytest.mark.django_db(transaction=True)
def test_database_prevents_duplicate_automatic_financial_entry(
    atomic_therapist,
    atomic_patient,
):
    start = timezone.now() + timedelta(days=1)
    appointment = Appointment.objects.create(
        patient=atomic_patient,
        therapist=atomic_therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value="150.00",
    )
    defaults = {
        "therapist": atomic_therapist,
        "patient": atomic_patient,
        "appointment": appointment,
        "source": FinancialTransaction.Source.APPOINTMENT,
        "transaction_type": FinancialTransaction.TransactionType.INCOME,
        "category": FinancialTransaction.Category.SESSION,
        "amount": "150.00",
    }
    FinancialTransaction.objects.create(**defaults)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            FinancialTransaction.objects.create(**defaults)
    assert (
        FinancialTransaction.objects.filter(
            appointment=appointment,
            source=FinancialTransaction.Source.APPOINTMENT,
        ).count()
        == 1
    )
