import os
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.billing.models import Plan, Subscription
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
)
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, TelemedicineRoom
from apps.scheduling.services.telemedicine import create_patient_invitation
from apps.users.models import User

user = User.objects.get(email=os.environ["E2E_USER_EMAIL"])
organization = Organization.objects.create(
    name="Clínica E2E Telemedicina",
    slug="clinica-e2e-telemedicina",
    organization_type=Organization.Type.CLINIC,
    status=Organization.Status.ACTIVE,
    created_by=user,
)
OrganizationSettings.objects.create(
    organization=organization,
    allow_telemedicine=True,
)
OrganizationMembership.objects.create(
    organization=organization,
    user=user,
    role=OrganizationMembership.Role.OWNER,
    status=OrganizationMembership.Status.ACTIVE,
    is_default=not OrganizationMembership.objects.filter(
        user=user,
        is_default=True,
    ).exists(),
)
plan = Plan.objects.create(
    name="Plano E2E Telemedicina",
    slug="plano-e2e-telemedicina",
    price=Decimal("99.00"),
    has_telemedicine=True,
)
now = timezone.now()
Subscription.objects.create(
    user=user,
    plan=plan,
    status=Subscription.Status.ACTIVE,
    started_at=now - timedelta(days=1),
    access_starts_at=now - timedelta(days=1),
    access_ends_at=now + timedelta(days=30),
)
patient = Patient.objects.create(
    organization=organization,
    therapist=user,
    full_name="Paciente E2E Telemedicina",
)
start = now + timedelta(minutes=5)
appointment = Appointment.objects.create(
    organization=organization,
    patient=patient,
    therapist=user,
    start_time=start,
    end_time=start + timedelta(minutes=50),
    status=Appointment.Status.CONFIRMED,
    modality=Appointment.Modality.ONLINE,
    session_value=Decimal("150.00"),
    created_by=user,
    updated_by=user,
)
room = TelemedicineRoom.objects.get(appointment=appointment)
_, raw_token, _ = create_patient_invitation(actor=user, room=room)

with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as env_file:
    env_file.write(f"E2E_TELEMEDICINE_TOKEN={raw_token}\n")
