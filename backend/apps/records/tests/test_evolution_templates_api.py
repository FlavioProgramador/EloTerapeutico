import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="template.terapeuta@teste.com",
        password="SenhaForte123!",
        full_name="Terapeuta Template",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def secretary(db):
    return User.objects.create_user(
        email="template.secretaria@teste.com",
        password="SenhaForte123!",
        full_name="Secretaria Template",
        role=User.Role.SECRETARY,
    )


@pytest.fixture
def client(therapist):
    api = APIClient()
    api.force_authenticate(therapist)
    return api


@pytest.fixture
def secretary_client(secretary):
    api = APIClient()
    api.force_authenticate(secretary)
    return api


@pytest.mark.django_db
def test_create_and_list_evolution_templates(client, therapist):
    payload = {
        "name": "Template de Avaliação",
        "description": "Uma avaliação completa",
        "category": "evaluation",
        "content": "# Avaliação\nConteúdo.",
    }
    # Criar
    response = client.post(reverse("clinical-evolution-templates"), payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    template_id = response.data["id"]

    # Listar
    list_response = client.get(reverse("clinical-evolution-templates"))
    assert list_response.status_code == status.HTTP_200_OK
    assert len(list_response.data) >= 1

    # Atualizar
    patch_response = client.patch(
        reverse("clinical-evolution-template-detail", args=[template_id]),
        {"name": "Template Modificado"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    assert patch_response.data["name"] == "Template Modificado"

    # Duplicar
    dup_response = client.post(
        reverse("clinical-evolution-template-detail", args=[template_id]),
        {"action": "duplicate"},
        format="json",
    )
    assert dup_response.status_code == status.HTTP_201_CREATED

    # Desativar (action)
    deact_response = client.post(
        reverse("clinical-evolution-template-detail", args=[template_id]),
        {"action": "deactivate"},
        format="json",
    )
    assert deact_response.status_code == status.HTTP_200_OK
    assert deact_response.data["is_active"] is False

    # Apagar (soft delete)
    del_response = client.delete(reverse("clinical-evolution-template-detail", args=[template_id]))
    assert del_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_secretary_cannot_access_templates(secretary_client):
    response = secretary_client.get(reverse("clinical-evolution-templates"))
    assert response.status_code == status.HTTP_403_FORBIDDEN
