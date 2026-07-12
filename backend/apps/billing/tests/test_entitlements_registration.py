from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.billing.models import Plan, PlanPrice, Subscription
from apps.billing.services.entitlements import get_entitlement
from apps.billing.services.features import can_use_feature, enforce_patient_limit
from apps.billing.services.trials import start_trial
from apps.patients.models import Patient


@override_settings(BILLING_REQUIRE_SUBSCRIPTION=True, BILLING_TRIAL_DAYS=7)
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
            name="Essencial Mensal",
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
            "phone": "21999999999",
            "plan": self.plan.slug,
            "access_mode": "TRIAL",
            "terms_accepted": True,
            "privacy_accepted": True,
        }
        payload.update(overrides)
        return payload

    def authenticate(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_registration_without_plan_creates_account_and_redirects_to_plans(self):
        payload = self.registration_payload()
        payload.pop("plan")

        response = self.client.post("/api/v1/auth/register/", payload, format="json")

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="novo.terapeuta@example.com")
        self.assertEqual(response.data["next"], "/planos")
        self.assertFalse(Subscription.objects.filter(user=user).exists())
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertIsNotNone(user.privacy_accepted_at)

    def test_registration_rejects_missing_legal_acceptance(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            self.registration_payload(terms_accepted=False),
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("terms_accepted", response.data)

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
        self.assertIsNotNone(user.trial_used_at)
        self.assertEqual(response.data["next"], "/onboarding")

    def test_paid_registration_creates_pending_local_subscription_before_checkout(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            self.registration_payload(access_mode="PAID"),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="novo.terapeuta@example.com")
        subscription = Subscription.objects.get(user=user)
        self.assertEqual(subscription.status, Subscription.Status.PENDING)
        self.assertIsNone(subscription.billing_order_id)
        self.assertTrue(subscription.metadata["awaiting_checkout"])
        self.assertIn("/checkout?", response.data["next"])
        self.assertIn(self.price.slug, response.data["next"])

    def test_trial_cannot_be_restarted_after_cancellation_or_plan_change(self):
        user = get_user_model().objects.create_user(
            email="trial.used@example.com",
            full_name="Trial Usado",
            password=self.password,
        )
        first = start_trial(user=user, plan_price=self.price)
        first.status = Subscription.Status.CANCELED
        first.canceled_at = timezone.now()
        first.save(update_fields=["status", "canceled_at", "updated_at"])

        with self.assertRaisesMessage(Exception, "já foi utilizado"):
            start_trial(user=user, plan_price=self.price)

        self.assertEqual(Subscription.objects.filter(user=user).count(), 1)

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
        start_trial(user=user, plan_price=self.price)
        self.authenticate(user)

        response = self.client.get("/api/v1/auth/working-hours/")

        self.assertEqual(response.status_code, 200)

    def test_past_due_user_is_blocked_even_inside_legacy_grace_period(self):
        user = get_user_model().objects.create_user(
            email="past.due@example.com",
            full_name="Pagamento Vencido",
            password=self.password,
        )
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=user,
            plan=self.plan,
            status=Subscription.Status.PAST_DUE,
            started_at=now,
            access_starts_at=now,
            access_ends_at=now + timedelta(days=30),
            grace_period_ends_at=now + timedelta(days=5),
        )
        self.authenticate(user)

        response = self.client.get("/api/v1/auth/working-hours/")
        decision = get_entitlement(user)

        self.assertEqual(response.status_code, 402)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "PAYMENT_PAST_DUE")
        self.assertEqual(decision.redirect_to, "/billing/past-due")
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.PAST_DUE)

    def test_expired_trial_is_persisted_as_expired_and_redirected(self):
        user = get_user_model().objects.create_user(
            email="expired.trial@example.com",
            full_name="Trial Expirado",
            password=self.password,
        )
        now = timezone.now()
        subscription = Subscription.objects.create(
            user=user,
            plan=self.plan,
            status=Subscription.Status.TRIALING,
            started_at=now - timedelta(days=8),
            access_starts_at=now - timedelta(days=8),
            access_ends_at=now - timedelta(days=1),
            trial_ends_at=now - timedelta(days=1),
        )

        decision = get_entitlement(user)
        subscription.refresh_from_db()

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "TRIAL_EXPIRED")
        self.assertEqual(decision.redirect_to, "/billing/expired")
        self.assertEqual(subscription.status, Subscription.Status.EXPIRED)

    def test_active_user_is_sent_to_onboarding_until_completed(self):
        user = get_user_model().objects.create_user(
            email="onboarding@example.com",
            full_name="Sem Onboarding",
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
        )

        decision = get_entitlement(user)

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.onboarding_required)
        self.assertEqual(decision.redirect_to, "/onboarding")

    def test_onboarding_endpoint_is_available_without_subscription(self):
        user = get_user_model().objects.create_user(
            email="onboarding.no.plan@example.com",
            full_name="Conta Sem Plano",
            password=self.password,
        )
        self.authenticate(user)

        response = self.client.post(
            "/api/v1/auth/onboarding/",
            {
                "clinic_name": "Clínica Elo",
                "specialty": "Psicologia",
                "complete": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.onboarding_completed)
        self.assertEqual(user.clinic_name, "Clínica Elo")
        self.assertEqual(response.data["next"], "/dashboard")

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
