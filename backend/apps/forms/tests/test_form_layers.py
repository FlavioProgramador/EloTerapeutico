from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.exceptions import InvalidFormAnswerError
from apps.forms.models import FieldType, FormField, FormSubmission, TherapeuticForm
from apps.forms.selectors import forms_for_owner
from apps.forms.services import create_submission, duplicate_form
from apps.organizations.models import Organization, OrganizationMembership, OrganizationSettings
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

    def test_form_submission_list_isolates_therapists_within_same_organization(self):
        org = Organization.objects.create(
            name="Clínica Elo",
            slug="clinica-elo",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.owner,
        )
        OrganizationSettings.objects.get_or_create(
            organization=org,
            business_name_on_documents=org.name,
        )
        OrganizationMembership.objects.create(
            organization=org,
            user=self.owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        OrganizationMembership.objects.create(
            organization=org,
            user=self.other_owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        org_form = TherapeuticForm.objects.create(
            organization=org,
            owner=self.owner,
            name="Formulário da Clínica",
            created_by=self.owner,
            updated_by=self.owner,
        )

        patient_1 = Patient.objects.create(
            organization=org,
            full_name="Paciente 1",
            therapist=self.owner,
        )
        patient_2 = Patient.objects.create(
            organization=org,
            full_name="Paciente 2",
            therapist=self.other_owner,
        )

        sub_1 = FormSubmission.objects.create(
            organization=org,
            form=org_form,
            patient=patient_1,
            professional=self.owner,
            owner=self.owner,
            submitted_by=self.owner,
        )
        sub_2 = FormSubmission.objects.create(
            organization=org,
            form=org_form,
            patient=patient_2,
            professional=self.other_owner,
            owner=self.other_owner,
            submitted_by=self.other_owner,
        )

        # Authenticate as therapist 1 (owner of org_form)
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.pk))
        response = self.client.get(f"/api/v1/forms/{org_form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        self.assertIn(sub_1.pk, ids)
        self.assertNotIn(sub_2.pk, ids)

        # Create form owned by therapist 2
        org_form_2 = TherapeuticForm.objects.create(
            organization=org,
            owner=self.other_owner,
            name="Formulário da Clínica 2",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )

        sub_3 = FormSubmission.objects.create(
            organization=org,
            form=org_form_2,
            patient=patient_2,
            professional=self.other_owner,
            owner=self.other_owner,
            submitted_by=self.other_owner,
        )
        sub_4 = FormSubmission.objects.create(
            organization=org,
            form=org_form_2,
            patient=patient_1,
            professional=self.owner,
            owner=self.owner,
            submitted_by=self.owner,
        )

        # Authenticate as therapist 2
        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.pk))
        response = self.client.get(f"/api/v1/forms/{org_form_2.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        ids = [item["id"] for item in results]
        self.assertIn(sub_3.pk, ids)
        self.assertNotIn(sub_4.pk, ids)
