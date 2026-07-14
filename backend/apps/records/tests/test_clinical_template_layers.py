from django.test import TestCase

from apps.records.models.templates import ClinicalEvolutionTemplate
from apps.records.selectors import clinical_templates_for_user
from apps.records.services import archive_clinical_template, duplicate_clinical_template
from apps.users.models import User


class ClinicalTemplateLayerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="records-owner@example.test",
            password="strong-password",
            full_name="Profissional Prontuário",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-records-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.private = ClinicalEvolutionTemplate.objects.create(
            owner=self.owner,
            name="Template privado",
            content="Evolução {{conteudo}}",
        )
        self.other_private = ClinicalEvolutionTemplate.objects.create(
            owner=self.other_owner,
            name="Template externo",
            content="Conteúdo externo",
        )
        self.system = ClinicalEvolutionTemplate.objects.create(
            owner=None,
            name="Template global",
            content="Conteúdo global",
        )

    def test_selector_returns_private_and_system_without_leaking_other_owner(self):
        self.assertQuerySetEqual(
            clinical_templates_for_user(user=self.owner),
            [self.system, self.private],
            ordered=False,
        )

    def test_duplicate_system_template_creates_private_copy(self):
        copy = duplicate_clinical_template(actor=self.owner, template=self.system)
        self.assertEqual(copy.owner, self.owner)
        self.assertEqual(copy.content, self.system.content)
        self.assertTrue(copy.name.startswith("Cópia de"))

    def test_archive_service_changes_state_atomically(self):
        template = archive_clinical_template(template=self.private)
        self.assertFalse(template.is_active)
        self.assertIsNotNone(template.archived_at)
