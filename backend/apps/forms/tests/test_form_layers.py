from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.exceptions import InvalidFormAnswerError
from apps.forms.models import FieldType, FormField, FormSubmission, TherapeuticForm
from apps.forms.selectors import forms_for_owner
from apps.forms.services import create_submission, duplicate_form
from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.users.models import User


class FormsLayerTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="forms-owner@example.test",
            password="strong-password",
            full_name="Profissional Formulários",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-forms-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(full_name="Paciente Formulários", therapist=self.owner)
        self.form = TherapeuticForm.objects.create(
            owner=self.owner,
            name="Formulário privado",
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.field = FormField.objects.create(
            form=self.form,
            type=FieldType.SHORT_TEXT,
            label="Como você está?",
            order=1,
        )
        self.other_form = TherapeuticForm.objects.create(
            owner=self.other_owner,
            name="Formulário externo",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )
        self.client.force_authenticate(self.owner)

    def test_form_selector_preserves_owner_boundary(self):
        self.assertQuerySetEqual(forms_for_owner(owner=self.owner), [self.form])

    def test_form_detail_does_not_expose_another_owner(self):
        response = self.client.get(f"/api/v1/forms/{self.other_form.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_duplicate_service_copies_fields_and_ownership(self):
        copy = duplicate_form(actor=self.owner, source=self.form)
        self.assertEqual(copy.owner, self.owner)
        self.assertEqual(copy.fields.count(), 1)
        copied_field = copy.fields.get()
        self.assertEqual(copied_field.label, self.field.label)
        self.assertNotEqual(copied_field.pk, self.field.pk)

    def test_invalid_answer_rolls_back_submission(self):
        with self.assertRaises(InvalidFormAnswerError):
            create_submission(
                form=self.form,
                validated_data={
                    "patient": self.patient,
                    "professional": self.owner,
                    "answers": [{"field": 999999, "value": "resposta"}],
                },
            )
        self.assertFalse(FormSubmission.objects.exists())


class FormSubmissionSecurityTests(APITestCase):
    def setUp(self):
        self.therapist_a = User.objects.create_user(
            email="therapist-a@example.test",
            password="strong-password",
            full_name="Terapeuta A",
            role=User.Role.THERAPIST,
        )
        self.org1 = Organization.objects.create(name="Clínica A", slug="clinica-a", created_by=self.therapist_a)
        OrganizationMembership.objects.create(
            user=self.therapist_a,
            organization=self.org1,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=True,
        )

        self.therapist_b = User.objects.create_user(
            email="therapist-b@example.test",
            password="strong-password",
            full_name="Terapeuta B",
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            user=self.therapist_b,
            organization=self.org1,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=True,
        )

        self.therapist_other_org = User.objects.create_user(
            email="therapist-other@example.test",
            password="strong-password",
            full_name="Terapeuta Outro Tenant",
            role=User.Role.THERAPIST,
        )
        self.org2 = Organization.objects.create(name="Clínica B", slug="clinica-b", created_by=self.therapist_other_org)
        OrganizationMembership.objects.create(
            user=self.therapist_other_org,
            organization=self.org2,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=True,
        )

        self.patient_a = Patient.objects.create(
            organization=self.org1,
            full_name="Paciente A",
            therapist=self.therapist_a,
        )
        self.patient_b = Patient.objects.create(
            organization=self.org1,
            full_name="Paciente B",
            therapist=self.therapist_b,
        )

        self.form_org1 = TherapeuticForm.objects.create(
            organization=self.org1,
            owner=self.therapist_a,
            name="Anamnese Org1",
            created_by=self.therapist_a,
            updated_by=self.therapist_a,
        )

        self.sub_a = FormSubmission.objects.create(
            organization=self.org1,
            form=self.form_org1,
            patient=self.patient_a,
            professional=self.therapist_a,
            owner=self.therapist_a,
        )
        self.sub_b = FormSubmission.objects.create(
            organization=self.org1,
            form=self.form_org1,
            patient=self.patient_b,
            professional=self.therapist_b,
            owner=self.therapist_b,
        )

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.get(f"/api/v1/forms/{self.form_org1.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_other_tenant_therapist_is_rejected(self):
        self.client.force_authenticate(self.therapist_other_org)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org2.id))
        response = self.client.get(f"/api/v1/forms/{self.form_org1.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_therapist_cannot_see_other_therapist_submissions(self):
        self.client.force_authenticate(self.therapist_a)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org1.id))
        response = self.client.get(f"/api/v1/forms/{self.form_org1.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get("results", response.data)
        sub_ids = [item["id"] for item in results]

        self.assertIn(self.sub_a.pk, sub_ids)
        self.assertNotIn(self.sub_b.pk, sub_ids)
