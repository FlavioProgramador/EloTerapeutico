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

    def test_unauthenticated_user_cannot_list_form_submissions(self):
        self.client.logout()
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_form_submissions_isolation_between_therapists(self):
        org = Organization.objects.create(
            name="Clínica Integrada",
            slug="clinica-integrada",
            status=Organization.Status.ACTIVE,
            created_by=self.owner,
        )
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

        org_form = TherapeuticForm.objects.create(
            owner=self.owner,
            organization=org,
            name="Formulário Organizacional",
            created_by=self.owner,
            updated_by=self.owner,
        )
        patient_1 = Patient.objects.create(full_name="Paciente T1", therapist=self.owner, organization=org)
        patient_2 = Patient.objects.create(full_name="Paciente T2", therapist=self.other_owner, organization=org)

        submission_t1 = FormSubmission.objects.create(
            form=org_form,
            organization=org,
            patient=patient_1,
            professional=self.owner,
            owner=self.owner,
            submitted_by=self.owner,
        )
        submission_t2 = FormSubmission.objects.create(
            form=org_form,
            organization=org,
            patient=patient_2,
            professional=self.other_owner,
            owner=self.other_owner,
            submitted_by=self.other_owner,
        )

        # Therapist 1 should only see their submission
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
        res_t1 = self.client.get(f"/api/v1/forms/{org_form.pk}/submissions/")
        self.assertEqual(res_t1.status_code, status.HTTP_200_OK)
        results_t1 = res_t1.data.get("results", res_t1.data)
        submission_ids_t1 = [item["id"] for item in results_t1]
        self.assertIn(submission_t1.pk, submission_ids_t1)
        self.assertNotIn(submission_t2.pk, submission_ids_t1)

        # Therapist 2 cannot access form owned by Therapist 1
        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
        res_t2_unauthorized_form = self.client.get(f"/api/v1/forms/{org_form.pk}/submissions/")
        self.assertEqual(res_t2_unauthorized_form.status_code, status.HTTP_404_NOT_FOUND)

        # Therapist 2 on their own form only sees their own submissions
        org_form_2 = TherapeuticForm.objects.create(
            owner=self.other_owner,
            organization=org,
            name="Formulário T2",
            created_by=self.other_owner,
            updated_by=self.other_owner,
        )
        submission_t2_own = FormSubmission.objects.create(
            form=org_form_2,
            organization=org,
            patient=patient_2,
            professional=self.other_owner,
            owner=self.other_owner,
            submitted_by=self.other_owner,
        )
        res_t2 = self.client.get(f"/api/v1/forms/{org_form_2.pk}/submissions/")
        self.assertEqual(res_t2.status_code, status.HTTP_200_OK)
        results_t2 = res_t2.data.get("results", res_t2.data)
        submission_ids_t2 = [item["id"] for item in results_t2]
        self.assertIn(submission_t2_own.pk, submission_ids_t2)

    def test_other_tenant_therapist_cannot_access_form_submissions(self):
        org1 = Organization.objects.create(
            name="Tenant 1",
            slug="tenant-1",
            status=Organization.Status.ACTIVE,
            created_by=self.owner,
        )
        org2 = Organization.objects.create(
            name="Tenant 2",
            slug="tenant-2",
            status=Organization.Status.ACTIVE,
            created_by=self.other_owner,
        )
        OrganizationMembership.objects.create(
            user=self.owner,
            organization=org1,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        OrganizationMembership.objects.create(
            user=self.other_owner,
            organization=org2,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        org1_form = TherapeuticForm.objects.create(
            owner=self.owner,
            organization=org1,
            name="Form Tenant 1",
            created_by=self.owner,
            updated_by=self.owner,
        )

        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org2.id))
        response = self.client.get(f"/api/v1/forms/{org1_form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
