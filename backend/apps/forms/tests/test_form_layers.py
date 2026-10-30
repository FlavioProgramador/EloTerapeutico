from rest_framework import status
from rest_framework.test import APIClient, APITestCase

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
        self.user_a = User.objects.create_user(
            email="therapist.a@example.test",
            password="strong-password",
            full_name="Therapist A",
            role=User.Role.THERAPIST,
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.user_a,
        )
        OrganizationMembership.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.user_b = User.objects.create_user(
            email="therapist.b@example.test",
            password="strong-password",
            full_name="Therapist B",
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            organization=self.org_a,
            user=self.user_b,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.user_c = User.objects.create_user(
            email="therapist.c@example.test",
            password="strong-password",
            full_name="Therapist C",
            role=User.Role.THERAPIST,
        )
        self.org_c = Organization.objects.create(
            name="Org C",
            slug="org-c",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.user_c,
        )
        OrganizationMembership.objects.create(
            organization=self.org_c,
            user=self.user_c,
            role=OrganizationMembership.Role.OWNER,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.patient_a = Patient.objects.create(
            organization=self.org_a,
            therapist=self.user_a,
            full_name="Patient A",
        )
        self.patient_b = Patient.objects.create(
            organization=self.org_a,
            therapist=self.user_b,
            full_name="Patient B",
        )
        self.form_a = TherapeuticForm.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            name="Formulário Avaliação Org A",
            created_by=self.user_a,
            updated_by=self.user_a,
        )

        self.sub_a = FormSubmission.objects.create(
            organization=self.org_a,
            form=self.form_a,
            patient=self.patient_a,
            professional=self.user_a,
            owner=self.user_a,
            status=FormSubmission.Status.SUBMITTED,
        )
        self.sub_b = FormSubmission.objects.create(
            organization=self.org_a,
            form=self.form_a,
            patient=self.patient_b,
            professional=self.user_b,
            owner=self.user_b,
            status=FormSubmission.Status.SUBMITTED,
        )

        self.client_a = APIClient()
        self.client_a.force_authenticate(self.user_a)
        self.client_a.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_a.pk))

        self.client_c = APIClient()
        self.client_c.force_authenticate(self.user_c)
        self.client_c.credentials(HTTP_X_ORGANIZATION_ID=str(self.org_c.pk))

    def test_unauthenticated_user_cannot_list_submissions(self):
        client = APIClient()
        response = client.get(f"/api/v1/forms/{self.form_a.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_other_tenant_user_cannot_access_form_submissions(self):
        response = self.client_c.get(f"/api/v1/forms/{self.form_a.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_therapist_cannot_see_other_therapist_form_submissions(self):
        response = self.client_a.get(f"/api/v1/forms/{self.form_a.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        submission_ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.sub_a.pk, submission_ids)
        self.assertNotIn(self.sub_b.pk, submission_ids)
