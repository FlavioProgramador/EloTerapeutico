from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.records.services.utils import render_markdown_safely, safe_url_fetcher
from apps.records.treatment_models import ClinicalExport

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def therapist_user():
    return User.objects.create_user(
        email="therapist@elo.com.br",
        password="password123",
        role="therapist",
        full_name="Dr. Terapeuta",
    )


@pytest.fixture
def other_therapist_user():
    return User.objects.create_user(
        email="other@elo.com.br",
        password="password123",
        role="therapist",
        full_name="Dr. Outro",
    )


@pytest.fixture
def patient_obj(therapist_user):
    return Patient.objects.create(
        full_name="Maria Silva",
        cpf="12345678901",
        therapist=therapist_user,
        status="active",
    )


# ── 1. TESTES DE UTILS (MARKDOWN E SSRF) ──────────────────────────────────────


def test_markdown_rendering_escapes_html():
    markdown = "Olá **mundo**! <script>alert(1)</script> *italico*\n- item 1\n- item 2"
    rendered = render_markdown_safely(markdown)
    # Deve escapar tags HTML perigosas
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered
    # Deve converter negrito
    assert "<strong>mundo</strong>" in rendered
    # Deve converter italico
    assert "<em>italico</em>" in rendered
    # Deve converter a lista
    assert "<ul>" in rendered
    assert "<li>item 1</li>" in rendered


def test_safe_url_fetcher_blocks_everything():
    with pytest.raises(ValueError) as exc_info:
        safe_url_fetcher("http://google.com")
    assert "Acesso a recursos externos bloqueado por segurança" in str(exc_info.value)

    with pytest.raises(ValueError):
        safe_url_fetcher("file:///etc/passwd")


# ── 2. TESTES DE PERMISSÕES E CONFIDENCIALIDADE ────────────────────────────────


@pytest.mark.django_db
def test_confidential_evolution_isolation(api_client, therapist_user, other_therapist_user, patient_obj):
    # Cria evolução confidencial pelo therapist_user
    evolution = Evolution.objects.create(
        patient=patient_obj,
        session_date=timezone.now().date(),
        content="Conteúdo confidencial",
        created_by=therapist_user,
        is_confidential=True,
    )

    # Outro terapeuta tenta visualizar a evolução confidencial (sem permissão especial)
    # Para garantir o vínculo de paciente, fazemos com que o paciente pertença a ele temporariamente
    patient_obj.therapist = other_therapist_user
    patient_obj.save()

    api_client.force_authenticate(user=other_therapist_user)

    # 1. Detalhe da Evolução deve retornar 403 Forbidden
    detail_url = reverse("clinical-evolution-detail", kwargs={"pk": evolution.id})
    response = api_client.get(detail_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 2. Listagem de Evoluções não deve retornar a evolução confidencial
    list_url = reverse("clinical-evolutions", kwargs={"patient_id": patient_obj.id})
    response = api_client.get(list_url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0

    # 3. Dá permissão de visualização e tenta novamente
    from django.contrib.auth.models import Permission

    permission = Permission.objects.get(codename="view_confidential_evolution")
    other_therapist_user.user_permissions.add(permission)
    # Força recarga de permissões no cache do django
    other_therapist_user = User.objects.get(pk=other_therapist_user.id)
    api_client.force_authenticate(user=other_therapist_user)

    response = api_client.get(detail_url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_export_confidential_evolution_permission(api_client, therapist_user, other_therapist_user, patient_obj):
    # Cria evolução confidencial pelo therapist_user
    Evolution.objects.create(
        patient=patient_obj,
        session_date=timezone.now().date(),
        content="Conteúdo confidencial",
        created_by=therapist_user,
        is_confidential=True,
    )

    # Associa paciente ao outro terapeuta para acesso geral
    patient_obj.therapist = other_therapist_user
    patient_obj.save()

    api_client.force_authenticate(user=other_therapist_user)

    # Tenta criar solicitação de exportação de prontuário com evolução confidencial criada por outro
    export_url = reverse("patient-exports", kwargs={"patient_id": patient_obj.id})
    response = api_client.post(export_url, {"export_type": "Completo", "period": "Todo o período"})
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Dá permissão de exportar e tenta de novo
    from django.contrib.auth.models import Permission

    permission = Permission.objects.get(codename="export_confidential_evolution")
    other_therapist_user.user_permissions.add(permission)
    other_therapist_user = User.objects.get(pk=other_therapist_user.id)
    api_client.force_authenticate(user=other_therapist_user)

    response = api_client.post(export_url, {"export_type": "Completo", "period": "Todo o período"})
    assert response.status_code == status.HTTP_201_CREATED


# ── 3. TESTES DO WORKER E FILA DE PROCESSAMENTO ────────────────────────────────


@pytest.mark.django_db
def test_export_worker_flow(therapist_user, patient_obj):
    # Cria evolução
    Evolution.objects.create(
        patient=patient_obj,
        session_date=timezone.now().date(),
        content="Histórico de evolução comum",
        created_by=therapist_user,
    )

    # Cria job PENDING
    job = ClinicalExport.objects.create(
        patient=patient_obj,
        export_type="Completo",
        period="Todo o período",
        filename="teste.pdf",
        created_by=therapist_user,
        status=ClinicalExport.Status.PENDING,
    )

    # Executa a lógica de processamento do worker manualmente
    from apps.records.management.commands.run_export_worker import Command

    cmd = Command()
    cmd.process_job(job)

    # Recarrega o job
    job.refresh_from_db()
    assert job.status == ClinicalExport.Status.COMPLETED
    assert job.size_bytes > 0
    assert job.file is not None
    assert job.file.name.endswith(".pdf")
    assert job.download_url == f"/api/v1/records/exports/{job.id}/download/"


@pytest.mark.django_db
def test_worker_recovery_and_retries(therapist_user, patient_obj):
    # Job preso em PROCESSING há mais de 10 min
    stuck_job = ClinicalExport.objects.create(
        patient=patient_obj,
        export_type="Completo",
        period="Todo o período",
        filename="teste2.pdf",
        created_by=therapist_user,
        status=ClinicalExport.Status.PROCESSING,
        started_at=timezone.now() - timedelta(minutes=15),
        retries=1,
    )

    from apps.records.management.commands.run_export_worker import Command

    cmd = Command()
    cmd.recover_stuck_jobs()

    stuck_job.refresh_from_db()
    # Deve retornar para PENDING e incrementar retries
    assert stuck_job.status == ClinicalExport.Status.PENDING
    assert stuck_job.retries == 2

    # Agora simula falha permanente (atinge limite de 3 tentativas)
    stuck_job.status = ClinicalExport.Status.PROCESSING
    stuck_job.started_at = timezone.now() - timedelta(minutes=15)
    stuck_job.retries = 3
    stuck_job.save()

    cmd.recover_stuck_jobs()
    stuck_job.refresh_from_db()
    assert stuck_job.status == ClinicalExport.Status.FAILED
    assert "Timeout" in stuck_job.error_message
