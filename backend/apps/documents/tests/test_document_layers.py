from django.test import TestCase

from apps.documents.models import DocumentTemplate
from apps.documents.selectors import get_accessible_patient, get_owned_template, owned_templates
from apps.documents.services import create_template, update_template
from apps.patients.models import Patient
from apps.users.models import User


class DocumentLayerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="document-owner@example.test",
            password="strong-password",
            full_name="Profissional Documentos",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-document-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(full_name="Paciente do proprietário", therapist=self.owner)
        self.other_patient = Patient.objects.create(full_name="Paciente externo", therapist=self.other_owner)
        self.template = DocumentTemplate.objects.create(
            owner=self.owner,
            name="Template privado",
            category="Declaração",
            document_type=DocumentTemplate.DocumentType.DECLARATION,
            content="Documento de {{paciente.nome}}.",
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.other_template = DocumentTemplate.objects.create(
            owner=self.other_owner,
            name="Template externo",
            category="Declaração",
            document_type=DocumentTemplate.DocumentType.DECLARATION,
            content="Documento externo.",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )

    def test_template_selector_preserves_owner_boundary(self):
        self.assertQuerySetEqual(owned_templates(owner=self.owner), [self.template])
        self.assertIsNone(get_owned_template(owner=self.owner, public_id=self.other_template.public_id))

    def test_patient_selector_preserves_therapist_boundary(self):
        self.assertEqual(get_accessible_patient(owner=self.owner, patient_id=self.patient.pk), self.patient)
        self.assertIsNone(get_accessible_patient(owner=self.owner, patient_id=self.other_patient.pk))

    def test_template_services_control_ownership_and_version(self):
        created = create_template(
            actor=self.owner,
            validated_data={
                "name": "Template criado pelo service",
                "category": "Relatório",
                "document_type": DocumentTemplate.DocumentType.REPORT,
                "content": "Relatório de {{paciente.nome}}.",
            },
        )
        self.assertEqual(created.owner, self.owner)
        self.assertEqual(created.created_by, self.owner)
        self.assertFalse(created.is_library_template)

        updated = update_template(
            actor=self.owner,
            template=created,
            validated_data={"description": "Descrição atualizada"},
        )
        self.assertEqual(updated.description, "Descrição atualizada")
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.updated_by, self.owner)
