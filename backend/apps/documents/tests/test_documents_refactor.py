"""Testes de regressão da organização e dos contratos do módulo documents."""

from importlib import import_module

import pytest

from apps.core.quality.rules import validate_documents_architecture
from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.services import (
    create_generated_document,
    prepare_document_download,
    remove_or_archive_document,
    remove_or_archive_template,
)
from apps.patients.models import Patient
from apps.users.models import User

pytestmark = pytest.mark.django_db


def _create_user(*, email: str) -> User:
    return User.objects.create_user(
        email=email,
        password="strong-password",
        full_name="Profissional Documentos",
        role=User.Role.THERAPIST,
    )


def _create_template(*, owner: User, name: str = "Template privado") -> DocumentTemplate:
    return DocumentTemplate.objects.create(
        owner=owner,
        name=name,
        category="Declaração",
        document_type=DocumentTemplate.DocumentType.DECLARATION,
        content="Documento de {{paciente.nome}}.",
        created_by=owner,
        updated_by=owner,
    )


def _create_document(*, owner: User, patient: Patient, template: DocumentTemplate) -> GeneratedDocument:
    return create_generated_document(
        actor=owner,
        patient=patient,
        template=template,
        title="Documento de teste",
    ).document


def test_canonical_and_legacy_modules_remain_importable():
    modules = [
        "apps.documents.api.v1.urls",
        "apps.documents.api.v1.permissions",
        "apps.documents.api.v1.serializers",
        "apps.documents.api.v1.views",
        "apps.documents.urls",
        "apps.documents.permissions",
        "apps.documents.permissions.clinical_documents",
        "apps.documents.serializers",
        "apps.documents.serializers.document_templates",
        "apps.documents.serializers.generated_documents",
        "apps.documents.views",
        "apps.documents.views.document_templates",
        "apps.documents.views.generated_documents",
    ]

    for module_name in modules:
        assert import_module(module_name) is not None


def test_documents_architecture_rule_accepts_current_tree():
    errors: list[str] = []
    validate_documents_architecture(errors)
    assert errors == []


def test_template_without_history_is_deleted():
    owner = _create_user(email="template-delete@example.test")
    template = _create_template(owner=owner)
    template_id = template.pk

    result = remove_or_archive_template(actor=owner, template=template)

    assert result.object_id == template_id
    assert result.archived is False
    assert result.template is None
    assert DocumentTemplate.objects.filter(pk=template_id).exists() is False


def test_template_with_generated_history_is_archived():
    owner = _create_user(email="template-archive@example.test")
    patient = Patient.objects.create(full_name="Paciente Histórico", therapist=owner)
    template = _create_template(owner=owner)
    _create_document(owner=owner, patient=patient, template=template)

    result = remove_or_archive_template(actor=owner, template=template)

    template.refresh_from_db()
    assert result.archived is True
    assert result.template == template
    assert template.status == DocumentTemplate.Status.ARCHIVED
    assert template.archived_at is not None


def test_draft_without_pdf_is_deleted():
    owner = _create_user(email="draft-delete@example.test")
    patient = Patient.objects.create(full_name="Paciente Rascunho", therapist=owner)
    template = _create_template(owner=owner)
    document = _create_document(owner=owner, patient=patient, template=template)
    document_id = document.pk

    result = remove_or_archive_document(actor=owner, document=document)

    assert result.object_id == document_id
    assert result.archived is False
    assert result.document is None
    assert GeneratedDocument.objects.filter(pk=document_id).exists() is False


def test_download_requires_completed_document():
    owner = _create_user(email="download-state@example.test")
    patient = Patient.objects.create(full_name="Paciente Download", therapist=owner)
    template = _create_template(owner=owner)
    document = _create_document(owner=owner, patient=patient, template=template)

    with pytest.raises(DocumentDomainError, match="ainda não está disponível"):
        prepare_document_download(actor=owner, document=document)


def test_removal_rejects_document_from_another_owner():
    owner = _create_user(email="document-owner@example.test")
    other_owner = _create_user(email="document-other@example.test")
    patient = Patient.objects.create(full_name="Paciente Isolado", therapist=owner)
    template = _create_template(owner=owner)
    document = _create_document(owner=owner, patient=patient, template=template)

    with pytest.raises(DocumentDomainError, match="não autorizado"):
        remove_or_archive_document(actor=other_owner, document=document)
