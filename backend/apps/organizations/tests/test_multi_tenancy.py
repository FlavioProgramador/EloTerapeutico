from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIRequestFactory

from apps.organizations.exceptions import OrganizationAccessDeniedError
from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.services.tenant_context import resolve_request_organization
from apps.patients.models import Patient
from apps.patients.selectors.patients import patients_accessible_to
from apps.users.models import User

pytestmark = pytest.mark.django_db


def create_user(email: str, *, role: str = User.Role.THERAPIST) -> User:
    return User.objects.create_user(
        email=email,
        full_name=email.split("@", 1)[0].title(),
        password="TestPass2026!",
        role=role,
    )


def create_organization(
    *,
    owner: User,
    name: str,
    organization_type: str = Organization.Type.INDIVIDUAL,
    default: bool = True,
) -> tuple[Organization, OrganizationMembership]:
    organization = Organization.objects.create(
        name=name,
        slug=f"{name.lower().replace(' ', '-')}-{owner.pk}",
        organization_type=organization_type,
        created_by=owner,
    )
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=default,
    )
    return organization, membership


def test_supports_individual_and_clinic_organizations():
    individual_owner = create_user("individual@example.test")
    clinic_owner = create_user("clinic@example.test")

    individual, _ = create_organization(
        owner=individual_owner,
        name="Consultório Individual",
        organization_type=Organization.Type.INDIVIDUAL,
    )
    clinic, _ = create_organization(
        owner=clinic_owner,
        name="Clínica Integrada",
        organization_type=Organization.Type.CLINIC,
    )

    assert individual.organization_type == Organization.Type.INDIVIDUAL
    assert clinic.organization_type == Organization.Type.CLINIC
    assert individual.document == ""


def test_membership_is_unique_per_user_and_organization():
    owner = create_user("membership@example.test")
    organization, _ = create_organization(owner=owner, name="Organização Única")

    with pytest.raises(IntegrityError), transaction.atomic():
        OrganizationMembership.objects.create(
            organization=organization,
            user=owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )


def test_only_one_default_membership_per_user():
    owner = create_user("default@example.test")
    first, _ = create_organization(owner=owner, name="Primeira", default=True)
    second = Organization.objects.create(
        name="Segunda",
        slug=f"segunda-{owner.pk}",
        organization_type=Organization.Type.CLINIC,
        created_by=owner,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        OrganizationMembership.objects.create(
            organization=second,
            user=owner,
            role=OrganizationMembership.Role.OWNER,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=True,
        )

    assert first.memberships.filter(is_default=True).count() == 1


def test_header_cannot_activate_another_users_organization():
    user_a = create_user("tenant-a@example.test")
    user_b = create_user("tenant-b@example.test")
    organization_a, membership_a = create_organization(
        owner=user_a,
        name="Tenant A",
    )
    organization_b, _ = create_organization(
        owner=user_b,
        name="Tenant B",
    )
    request = APIRequestFactory().get(
        "/api/v1/organizations/context/",
        HTTP_X_ORGANIZATION_ID=str(organization_b.pk),
    )

    with pytest.raises(OrganizationAccessDeniedError):
        resolve_request_organization(request=request, user=user_a, required=True)

    request = APIRequestFactory().get(
        "/api/v1/organizations/context/",
        HTTP_X_ORGANIZATION_ID=str(organization_a.pk),
    )
    resolved_organization, resolved_membership = resolve_request_organization(
        request=request,
        user=user_a,
        required=True,
    )
    assert resolved_organization == organization_a
    assert resolved_membership == membership_a


def test_patient_selector_never_returns_another_tenant():
    therapist_a = create_user("therapist-a@example.test")
    therapist_b = create_user("therapist-b@example.test")
    organization_a, membership_a = create_organization(
        owner=therapist_a,
        name="Tenant Pacientes A",
    )
    organization_b, _ = create_organization(
        owner=therapist_b,
        name="Tenant Pacientes B",
    )
    patient_a = Patient.objects.create(
        organization=organization_a,
        therapist=therapist_a,
        full_name="Paciente A",
    )
    Patient.objects.create(
        organization=organization_b,
        therapist=therapist_b,
        full_name="Paciente B",
    )

    queryset = patients_accessible_to(
        therapist_a,
        organization=organization_a,
        membership=membership_a,
    )

    assert list(queryset.values_list("pk", flat=True)) == [patient_a.pk]
