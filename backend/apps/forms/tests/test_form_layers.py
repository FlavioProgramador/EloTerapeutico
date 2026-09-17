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

    def test_form_submission_list_unauthenticated_rejected(self):
        self.client.logout()
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_form_submission_list_therapist_isolation(self):
        org = Organization.objects.create(name="Clínica Elo", slug="clinica-elo", created_by=self.owner)
        OrganizationMembership.objects.create(
            organization=org,
            user=self.owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=False,
        )
        OrganizationMembership.objects.create(
            organization=org,
            user=self.other_owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
            is_default=False,
        )

        org_form = TherapeuticForm.objects.create(
            organization=org,
            owner=self.other_owner,
            name="Formulário da Clínica",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )

        patient1 = Patient.objects.create(full_name="Paciente 1", therapist=self.owner)
        patient2 = Patient.objects.create(full_name="Paciente 2", therapist=self.other_owner)

        sub1 = FormSubmission.objects.create(
            organization=org,
            form=org_form,
            patient=patient1,
            professional=self.owner,
            owner=self.owner,
            submitted_by=self.owner,
        )
        sub2 = FormSubmission.objects.create(
            organization=org,
            form=org_form,
            patient=patient2,
            professional=self.other_owner,
            owner=self.other_owner,
            submitted_by=self.other_owner,
        )

        headers = {"X-Organization-Id": str(org.pk)}

        # Authenticated as self.other_owner (therapist 2 who owns org_form)
        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.pk))
        res = self.client.get(f"/api/v1/forms/{org_form.pk}/submissions/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", res.data)
        submission_ids = [item["id"] for item in results]
        self.assertIn(str(sub2.pk), [str(i) for i in submission_ids])
        self.assertNotIn(str(sub1.pk), [str(i) for i in submission_ids])
