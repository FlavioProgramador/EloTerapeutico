from datetime import date

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.treatment_models import ClinicalExport
from apps.users.models import User


@pytest.fixture
def export_context(db):
    therapist = User.objects.create_user(
        email="export.owner@example.com",
        password="password",
        full_name="Terapeuta Exportação",
        role=User.Role.THERAPIST,
    )
    admin = User.objects.create_user(
        email="export.admin@example.com",
        password="password",
        full_name="Administrador Exportação",
        role=User.Role.ADMIN,
    )
    patient = Patient.objects.create(
        full_name="Paciente Exportação",
        cpf="98765432100",
        birth_date=date(1991, 1, 1),
        therapist=therapist,
    )

    owner_client = APIClient()
    owner_client.force_authenticate(therapist)
    admin_client = APIClient()
    admin_client.force_authenticate(admin)

    return {
        "therapist": therapist,
        "admin": admin,
        "patient": patient,
        "owner_client": owner_client,
        "admin_client": admin_client,
    }


def create_export(*, patient, created_by, status=ClinicalExport.Status.COMPLETED, suffix="owner"):
    export_obj = ClinicalExport.objects.create(
        patient=patient,
        created_by=created_by,
        export_type="FULL_RECORD",
        filename=f"prontuario_{suffix}.pdf",
        status=status,
    )
    if status == ClinicalExport.Status.COMPLETED:
        export_obj.file = SimpleUploadedFile(
            f"prontuario_{suffix}.pdf",
            b"%PDF-1.4\n%%EOF",
            content_type="application/pdf",
        )
        export_obj.size_bytes = export_obj.file.size
        export_obj.save(update_fields=["file", "size_bytes"])
    return export_obj


@pytest.mark.django_db
def test_criador_baixa_exportacao_com_headers_privados(export_context):
    export_obj = create_export(
        patient=export_context["patient"],
        created_by=export_context["therapist"],
    )

    response = export_context["owner_client"].get(
        f"/api/v1/records/exports/{export_obj.id}/download/"
    )

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["Expires"] == "0"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cross-Origin-Resource-Policy"] == "same-origin"


@pytest.mark.django_db
def test_admin_sem_permissao_explicita_nao_baixa_exportacao_de_outro_profissional(export_context):
    export_obj = create_export(
        patient=export_context["patient"],
        created_by=export_context["therapist"],
    )

    response = export_context["admin_client"].get(
        f"/api/v1/records/exports/{export_obj.id}/download/"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_com_permissao_explicita_baixa_exportacao_de_outro_profissional(export_context):
    export_obj = create_export(
        patient=export_context["patient"],
        created_by=export_context["therapist"],
    )
    permission = Permission.objects.get(
        codename="export_confidential_evolution",
        content_type__app_label="records",
    )
    export_context["admin"].user_permissions.add(permission)
    export_context["admin"].refresh_from_db()
    export_context["admin_client"].force_authenticate(export_context["admin"])

    response = export_context["admin_client"].get(
        f"/api/v1/records/exports/{export_obj.id}/download/"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_sem_permissao_lista_apenas_exportacoes_proprias(export_context):
    foreign_export = create_export(
        patient=export_context["patient"],
        created_by=export_context["therapist"],
        suffix="foreign",
    )
    own_export = create_export(
        patient=export_context["patient"],
        created_by=export_context["admin"],
        suffix="admin",
    )

    response = export_context["admin_client"].get(
        f"/api/v1/records/patients/{export_context['patient'].id}/exports/"
    )

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data}
    assert own_export.id in returned_ids
    assert foreign_export.id not in returned_ids


@pytest.mark.django_db
def test_admin_sem_permissao_nao_reprocessa_exportacao_de_outro_profissional(export_context):
    export_obj = create_export(
        patient=export_context["patient"],
        created_by=export_context["therapist"],
        status=ClinicalExport.Status.FAILED,
    )

    response = export_context["admin_client"].post(
        f"/api/v1/records/exports/{export_obj.id}/retry/",
        {},
        format="json",
    )

    assert response.status_code == 403
