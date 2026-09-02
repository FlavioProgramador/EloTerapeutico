from rest_framework import status
from rest_framework.test import APITestCase

from apps.forms.exceptions import InvalidFormAnswerError
from apps.forms.models import FieldType, FormField, FormSubmission, TherapeuticForm
from apps.forms.selectors import forms_for_owner
from apps.forms.services import create_submission, duplicate_form
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

    def test_form_submission_listing_isolation(self):
        from apps.organizations.models import Organization, OrganizationMembership

        org = Organization.objects.create(name="Clínica Teste", slug="clinica-teste", created_by=self.owner)
        OrganizationMembership.objects.create(
            user=self.owner,
            organization=org,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        OrganizationMembership.objects.create(
            user=self.other_owner,
            organization=org,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.form.organization = org
        self.form.save()

        sub_owner = FormSubmission.objects.create(
            form=self.form,
            organization=org,
            owner=self.owner,
            professional=self.owner,
            submitted_by=self.owner,
        )
        sub_other = FormSubmission.objects.create(
            form=self.form,
            organization=org,
            owner=self.other_owner,
            professional=self.other_owner,
            submitted_by=self.other_owner,
        )

        # 1. Unauthenticated request is rejected
        self.client.logout()
        res_unauth = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertIn(res_unauth.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # 2. Authenticated as owner (Therapist A)
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
        res_owner = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)
        results_owner = res_owner.data.get("results", res_owner.data)
        ids_owner = [item["id"] for item in results_owner]
        self.assertIn(sub_owner.pk, ids_owner)
        self.assertNotIn(sub_other.pk, ids_owner)
