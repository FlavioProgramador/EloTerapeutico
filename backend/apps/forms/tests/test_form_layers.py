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

    def test_list_form_submissions_unauthenticated_rejected(self):
        self.client.logout()
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_form_submissions_therapist_isolation(self):
        org_a = Organization.objects.create(name="Org A", slug="org-a", created_by=self.owner)
        OrganizationMembership.objects.create(
            organization=org_a,
            user=self.owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        self.form.organization = org_a
        self.form.save()
        self.patient.organization = org_a
        self.patient.save()

        submission = FormSubmission.objects.create(
            organization=org_a,
            form=self.form,
            patient=self.patient,
            professional=self.owner,
            owner=self.owner,
            status=FormSubmission.Status.SUBMITTED,
        )

        # Authorized owner/therapist lists submissions
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.id))
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], submission.pk)

        # Therapist in same org without form ownership gets 404 for another therapist's form
        other_therapist_same_org = User.objects.create_user(
            email="therapist-same-org@example.test",
            password="strong-password",
            full_name="Therapist Same Org",
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            organization=org_a,
            user=other_therapist_same_org,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        self.client.force_authenticate(other_therapist_same_org)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.id))
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Therapist creates their own form in org_a
        shared_form = TherapeuticForm.objects.create(
            organization=org_a,
            owner=other_therapist_same_org,
            name="Formulário do Outro Terapeuta",
            created_by=other_therapist_same_org,
            updated_by=other_therapist_same_org,
        )

        # Create submission belonging to self.owner and submission belonging to other_therapist_same_org
        FormSubmission.objects.create(
            organization=org_a,
            form=shared_form,
            patient=self.patient,
            professional=self.owner,
            owner=self.owner,
            status=FormSubmission.Status.SUBMITTED,
        )
        other_submission = FormSubmission.objects.create(
            organization=org_a,
            form=shared_form,
            patient=self.patient,
            professional=other_therapist_same_org,
            owner=other_therapist_same_org,
            status=FormSubmission.Status.SUBMITTED,
        )

        # when other_therapist_same_org lists submissions, only other_submission is returned
        response = self.client.get(f"/api/v1/forms/{shared_form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], other_submission.pk)

        # Therapist from another tenant cannot access form at all
        org_b = Organization.objects.create(name="Org B", slug="org-b", created_by=self.other_owner)
        OrganizationMembership.objects.create(
            organization=org_b,
            user=self.other_owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )
        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(org_b.id))
        response = self.client.get(f"/api/v1/forms/{self.form.pk}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
