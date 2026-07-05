from unittest.mock import patch

from django.core.files.storage import default_storage
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.patients.models import Patient
from apps.users.models import User


@override_settings(MEDIA_ROOT="/tmp/elo-terapeutico-document-tests")
class DocumentModuleApiTests(APITestCase):
    def setUp(self):
        self.therapist = User.objects.create_user(
            email="therapist@example.test",
            password="strong-password",
            full_name="Profissional Teste",
            role=User.Role.THERAPIST,
            specialty="Psicologia",
            crp_number="06/123456",
        )
        self.other_therapist = User.objects.create_user(
            email="other@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(
            full_name="Paciente Exemplo",
            therapist=self.therapist,
        )
        self.other_patient = Patient.objects.create(
            full_name="Paciente de Outro Profissional",
            therapist=self.other_therapist,
        )
        self.template = DocumentTemplate.objects.create(
            owner=self.therapist,
            name="Declaração particular",
            category="Declaração",
            document_type=DocumentTemplate.DocumentType.DECLARATION,
            content="Declaro que {{paciente.nome_completo}} está em acompanhamento.",
            created_by=self.therapist,
            updated_by=self.therapist,
        )
        self.client.force_authenticate(self.therapist)

    def tearDown(self):
        for document in GeneratedDocument.objects.exclude(pdf_file=""):
            if document.pdf_file and default_storage.exists(document.pdf_file.name):
                default_storage.delete(document.pdf_file.name)

    def test_rejects_unknown_placeholder(self):
        response = self.client.post(
            "/api/v1/documents/templates/",
            {
                "name": "Template inválido",
                "category": "Declaração",
                "document_type": "declaration",
                "content": "{{paciente.senha}}",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("content", response.data["error"]["details"])

    def test_does_not_allow_generating_for_another_therapists_patient(self):
        response = self.client.post(
            "/api/v1/documents/generated/",
            {
                "template_public_id": str(self.template.public_id),
                "patient_id": self.other_patient.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("patient_id", response.data["error"]["details"])

    def test_creation_is_idempotent_and_stores_snapshot(self):
        payload = {
            "template_public_id": str(self.template.public_id),
            "patient_id": self.patient.pk,
        }
        first = self.client.post(
            "/api/v1/documents/generated/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-request",
        )
        second = self.client.post(
            "/api/v1/documents/generated/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="same-request",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["public_id"], second.data["public_id"])
        document = GeneratedDocument.objects.get(public_id=first.data["public_id"])
        self.template.content = "Conteúdo alterado depois da geração."
        self.template.save(update_fields=["content", "updated_at"])
        self.assertIn("Paciente Exemplo", document.rendered_content)
        self.assertNotEqual(document.template_content_snapshot, self.template.content)

    @patch("apps.documents.services.HTML")
    def test_generates_private_pdf_and_hash(self, html_mock):
        html_mock.return_value.write_pdf.return_value = b"%PDF-safe-test"
        create_response = self.client.post(
            "/api/v1/documents/generated/",
            {
                "template_public_id": str(self.template.public_id),
                "patient_id": self.patient.pk,
            },
            format="json",
        )
        public_id = create_response.data["public_id"]
        generate_response = self.client.post(
            f"/api/v1/documents/generated/{public_id}/generate/",
            {},
            format="json",
        )
        self.assertEqual(generate_response.status_code, status.HTTP_200_OK)
        self.assertEqual(generate_response.data["status"], "completed")
        self.assertTrue(generate_response.data["pdf_hash"])
        download = self.client.get(
            f"/api/v1/documents/generated/{public_id}/download/"
        )
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download["Cache-Control"], "private, no-store, max-age=0")

    def test_library_import_creates_private_copy_only_once(self):
        library = DocumentTemplate.objects.create(
            owner=None,
            name="Modelo global para teste",
            category="Relatório",
            document_type=DocumentTemplate.DocumentType.REPORT,
            content="Relatório de {{paciente.nome}}.",
            is_library_template=True,
        )
        first = self.client.post(
            f"/api/v1/documents/library/{library.public_id}/import/",
            {},
            format="json",
        )
        second = self.client.post(
            f"/api/v1/documents/library/{library.public_id}/import/",
            {},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(
            DocumentTemplate.objects.filter(
                owner=self.therapist,
                source_library_template=library,
            ).count(),
            1,
        )
