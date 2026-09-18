import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.forms.models import FieldType, FormField, TherapeuticForm
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


def _create_tenant(user: User, slug: str) -> Organization:
    organization = Organization.objects.create(
        name=f"Organização de {user.full_name}",
        slug=slug,
        organization_type=Organization.Type.INDIVIDUAL,
        status=Organization.Status.ACTIVE,
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    user.test_organization = organization
    return organization


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email="forms.perf.therapist@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Forms Perf",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    _create_tenant(user, "forms-perf-therapist")
    return user


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    api_client.credentials(
        HTTP_X_ORGANIZATION_ID=str(therapist.test_organization.pk)
    )
    return api_client


def create_forms_with_fields(therapist, count):
    organization = therapist.test_organization
    for i in range(count):
        form = TherapeuticForm.objects.create(
            organization=organization,
            owner=therapist,
            created_by=therapist,
            updated_by=therapist,
            name=f"Formulário Perf {i}",
            description=f"Descrição {i}",
        )
        FormField.objects.create(
            form=form,
            type=FieldType.SHORT_TEXT,
            label=f"Campo 1 do Formulário {i}",
            order=1,
        )
        FormField.objects.create(
            form=form,
            type=FieldType.LONG_TEXT,
            label=f"Campo 2 do Formulário {i}",
            order=2,
        )


@pytest.mark.django_db
def test_form_list_queries_optimized(client, therapist):
    url = "/api/v1/forms/"

    # Warm up to avoid initial auth/session/content-type queries
    client.get(url)

    # 1. Setup 2 forms
    create_forms_with_fields(therapist, 2)

    with CaptureQueriesContext(connection) as queries_small:
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 2
        count_small = len(queries_small)

    # Clean up before creating larger dataset
    TherapeuticForm.objects.all().delete()

    # 2. Setup 5 forms
    create_forms_with_fields(therapist, 5)

    with CaptureQueriesContext(connection) as queries_large:
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        count_large = len(queries_large)

    print(f"\nForm list query count (2 items): {count_small}")
    print(f"Form list query count (5 items): {count_large}")

    # Prior to optimization, fields_count caused an extra SELECT COUNT(*) query per form (N+1 queries).
    # After utilizing _prefetched_objects_cache in SerializerMethodField, query count is constant.
    assert count_large == count_small
