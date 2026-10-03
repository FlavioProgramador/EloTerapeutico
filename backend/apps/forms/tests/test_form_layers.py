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
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.owner,
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.other_owner,
        )
        OrganizationMembership.objects.create(
            organization=self.org_a,
            user=self.owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b,
            user=self.other_owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.patient = Patient.objects.create(
            full_name="Paciente Formulários",
            therapist=self.owner,
            organization=self.org_a,
        )
        self.form = TherapeuticForm.objects.create(
            owner=self.owner,
            organization=self.org_a,
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
            organization=self.org_b,
            name="Formulário externo",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_a.pk))

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

    def test_form_submissions_unauthenticated_rejected(self):
        self.client.logout()
        self.client.credentials()
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_submissions_cross_tenant_rejected(self):
        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_b.pk))
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_form_submissions_therapist_isolation_same_org(self):
        therapist_2 = User.objects.create_user(
            email="therapist2@example.test",
            password="strong-password",
            full_name="Segundo Terapeuta",
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            organization=self.org_a,
            user=therapist_2,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        patient_2 = Patient.objects.create(
            full_name="Paciente 2",
            therapist=therapist_2,
            organization=self.org_a,
        )

        sub_1 = FormSubmission.objects.create(
            organization=self.org_a,
            form=self.form,
            patient=self.patient,
            professional=self.owner,
            owner=self.owner,
        )
        sub_2 = FormSubmission.objects.create(
            organization=self.org_a,
            form=self.form,
            patient=patient_2,
            professional=therapist_2,
            owner=therapist_2,
        )

        # Therapist 1 (self.owner) owns the form and lists submissions.
        # Should only see sub_1 (their patient's submission) and NOT sub_2 (therapist_2's patient's submission).
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_a.pk))
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], sub_1.pk)
