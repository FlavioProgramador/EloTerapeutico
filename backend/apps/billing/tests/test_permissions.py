from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Plan, Subscription
from apps.billing.services.features import can_use_feature, enforce_patient_limit
from apps.patients.models import Patient


class BillingPermissionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
        )
        self.basic_plan = Plan.objects.create(
            name="Essencial",
            slug="essencial-test",
            price="49.90",
            max_patients=1,
            has_financial=False,
            has_reports=False,
        )
        self.pro_plan = Plan.objects.create(
            name="Profissional",
            slug="profissional-test",
            price="89.90",
            max_patients=None,
            has_financial=True,
            has_reports=True,
        )

    def test_user_without_subscription_cannot_access_premium_feature(self):
        self.assertFalse(can_use_feature(self.user, "financial"))

    def test_user_with_plan_without_feature_cannot_access_resource(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status=Subscription.Status.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self.assertFalse(can_use_feature(self.user, "financial"))

    def test_user_with_feature_can_access_resource(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.pro_plan,
            status=Subscription.Status.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        self.assertTrue(can_use_feature(self.user, "financial"))

    @override_settings(BILLING_ENFORCE_PATIENT_LIMITS=True)
    def test_max_patients_limit_blocks_creation(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.basic_plan,
            status=Subscription.Status.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30),
        )
        Patient.objects.create(full_name="Paciente Um", therapist=self.user)

        with self.assertRaises(ValidationError):
            enforce_patient_limit(self.user)
