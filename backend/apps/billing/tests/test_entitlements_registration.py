from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.billing.models import Plan, PlanPrice, Subscription
from apps.billing.services.features import can_use_feature, enforce_patient_limit
from apps.patients.models import Patient


@override_settings(BILLING_REQUIRE_SUBSCRIPTION=True)
class SubscriptionRegistrationAndAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.plan = Plan.objects.create(
            name="Essencial",
            slug="essencial-access-test",
            description="Plano de teste",
            price="49.90",
            has_patients=False,
            max_patients=None,
        )
        self.price = PlanPrice.objects.create(
            plan=self.plan,
            name="Profissional Mensal",
            slug="essencial-mensal-access-test",
            total_amount="49.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
            trial_days=7,
        )
        self.password = f"Aa1!{get_random_string(24)}"

    def registration_payload(self, **overrides):
        payload = {
            "email": "novo.terapeuta@example.com",
            "full_name": "Novo Terapeuta",
            "password": self.password,
            "password_confirm": self.password,
            "specialty": "Psicologia clínica",
            "plan": self.plan.slug,
            "access_mode": "TRIAL",
        }
        payload.update(overrides)
        return payload

    def authenticate(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_registration_requires_selected_plan(self):
        payload = self.registration_payload()
        payload.pop("plan")

        response = self.client.post("/api/v1/auth/register/", payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_trial_registration_creates_exact_seven_day_access(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            self.registration_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="novo.terapeuta@example.com")
        subscription = Subscription.objects.get(user=user)
        self.assertEqual(subscription.status, Subscription.Status.TRIALING)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.trial_ends_at - subscription.started_at, timedelta(days=7))
        self.assertEqual(subscription.access_ends_at, subscription.trial_ends_at)
        self.assertTrue(subscription.has_access)
        self.assertEqual(response.data["next"], "/dashboard")

    def test_user_without_subscription_is_blocked_from_private_api(self):
        user = get_user_model().objects.create_user(
            email="sem.plano@example.com",
            full_name="Sem Plano",
            password=self.password,
        )
        self.authenticate(user)

        response = self.client.get("/api/v1/auth/working-hours/")

        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.data["error"]["code"], "SUBSCRIPTION_REQUIRED")

    def test_trial_user_can_access_private_api(self):
        user = get_user_model().objects.create_user(
            email="trial@example.com",
            full_name="Terapeuta Trial",
            password=self.password,
        )
        now = timezone.now()
        Subscription.objects.create(
            user=user,
            plan=self.plan,
            status=Subscription.Status.TRIALING,
            started_at=now,
            access_starts_at=now,
            access_ends_at=now + timedelta(days=7),
            trial_ends_at=now + timedelta(days=7),
        )
        self.authenticate(user)

        response = self.client.get("/api/v1/auth/working-hours/")

        self.assertEqual(response.status_code, 200)

    def test_patients_are_available_even_when_legacy_plan_flag_is_false(self):
        user = get_user_model().objects.create_user(
            email="pacientes@example.com",
            full_name="Terapeuta Pacientes",
            password=self.password,
        )
        now = timezone.now()
        Subscription.objects.create(
            user=user,
            plan=self.plan,
            status=Subscription.Status.ACTIVE,
            started_at=now,
            access_starts_at=now,
            access_ends_at=now + timedelta(days=30),
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

        self.assertTrue(can_use_feature(user, "patients"))
        enforce_patient_limit(user)

    def test_patient_tags_none_are_normalized_to_empty_list(self):
        user = get_user_model().objects.create_user(
            email="admin.patient@example.com",
            full_name="Terapeuta Admin",
            password=self.password,
        )

        patient = Patient.objects.create(
            full_name="Paciente sem etiquetas",
            therapist=user,
            tags=None,
        )

        patient.refresh_from_db()
        self.assertEqual(patient.tags, [])

    def test_admin_can_save_patient_with_empty_tags(self):
        user_model = get_user_model()
        administrator = user_model.objects.create_superuser(
            email="superuser@example.com",
            full_name="Administrador",
            password=self.password,
        )
        therapist = user_model.objects.create_user(
            email="therapist.admin@example.com",
            full_name="Terapeuta do Admin",
            password=self.password,
        )
        request = RequestFactory().post("/admin/patients/patient/add/")
        request.user = administrator
        model_admin = admin.site._registry[Patient]
        form_class = model_admin.get_form(request)
        form = form_class(
            data={
                "full_name": "Paciente cadastrado no admin",
                "therapist": str(therapist.pk),
                "gender": Patient.Gender.PREFER_NOT_TO_SAY,
                "status": Patient.Status.ACTIVE,
                "attendance_type": Patient.AttendanceType.INDIVIDUAL,
                "modality": Patient.Modality.IN_PERSON,
                "payer_type": Patient.PayerType.PRIVATE,
                "session_value": "120.00",
                "reminders_enabled": "on",
                "reminder_recipient": Patient.ReminderRecipient.PATIENT,
                "address": "{}",
                "tags": "",
                "is_active": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors.as_json())
        patient = form.save(commit=False)
        model_admin.save_model(request, patient, form, change=False)
        patient.refresh_from_db()
        self.assertEqual(patient.tags, [])
