from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import BillingOrder, Payment, PlanPrice, Subscription


class SubscriptionAccessService:
    ACTIVATABLE = {
        Subscription.Status.TRIALING,
        Subscription.Status.PENDING,
        Subscription.Status.ACTIVE,
        Subscription.Status.PAST_DUE,
        Subscription.Status.SUSPENDED,
    }

    @staticmethod
    def _period_end(start, billing_interval: str):
        if billing_interval == PlanPrice.BillingInterval.YEARLY:
            return start + relativedelta(years=1)
        return start + relativedelta(months=1)

    @classmethod
    @transaction.atomic
    def activate_from_payment(cls, subscription: Subscription, payment: Payment) -> Subscription:
        locked_subscription = (
            Subscription.objects.select_for_update()
            .select_related("plan", "billing_order", "billing_order__plan_price")
            .get(pk=subscription.pk)
        )
        locked_payment = Payment.objects.select_for_update().select_related("billing_order").get(pk=payment.pk)
        if locked_subscription.status not in cls.ACTIVATABLE:
            raise ValidationError("A assinatura não permite ativação neste estado.")
        if locked_payment.user_id != locked_subscription.user_id:
            raise ValidationError("Pagamento não pertence ao usuário da assinatura.")

        activation_key = locked_payment.gateway_payment_id or f"local:{locked_payment.pk}"
        metadata = dict(locked_subscription.metadata or {})
        if metadata.get("last_activated_payment_id") == activation_key:
            return locked_subscription

        order = locked_payment.billing_order or locked_subscription.billing_order
        interval = order.billing_interval if order else PlanPrice.BillingInterval.MONTHLY
        paid_at = locked_payment.paid_at or locked_payment.confirmed_at or timezone.now()
        is_plan_change = bool(
            order
            and (order.metadata or {}).get("is_plan_change")
            and locked_subscription.billing_order_id != order.pk
        )
        was_trial = locked_subscription.status == Subscription.Status.TRIALING

        if (
            order
            and order.billing_model == PlanPrice.BillingModel.INSTALLMENT
            and locked_subscription.started_at
            and not is_plan_change
        ):
            period_start = locked_subscription.access_starts_at or locked_subscription.started_at
            period_end = locked_subscription.access_ends_at or cls._period_end(period_start, interval)
        else:
            period_start = paid_at
            period_end = cls._period_end(period_start, interval)

        previous_plan_id = locked_subscription.plan_id
        previous_order_id = locked_subscription.billing_order_id
        previous_gateway_subscription_id = locked_subscription.gateway_subscription_id
        was_suspended = locked_subscription.status == Subscription.Status.SUSPENDED

        locked_subscription.status = Subscription.Status.ACTIVE
        locked_subscription.plan = order.plan if order else locked_subscription.plan
        locked_subscription.billing_order = order or locked_subscription.billing_order
        locked_subscription.started_at = paid_at if is_plan_change else (locked_subscription.started_at or paid_at)
        locked_subscription.access_starts_at = period_start
        locked_subscription.access_ends_at = period_end
        locked_subscription.current_period_start = period_start
        locked_subscription.current_period_end = period_end
        locked_subscription.trial_ends_at = None if was_trial else locked_subscription.trial_ends_at
        locked_subscription.grace_period_ends_at = None
        locked_subscription.suspended_at = None
        locked_subscription.reactivated_at = timezone.now() if was_suspended else locked_subscription.reactivated_at
        locked_subscription.canceled_at = None
        locked_subscription.cancel_at_period_end = False
        if order:
            locked_subscription.gateway_customer_id = order.gateway_customer_id or locked_subscription.gateway_customer_id
            locked_subscription.gateway_subscription_id = order.gateway_subscription_id
            locked_subscription.gateway_status = locked_payment.status

        pending_checkout = dict(metadata.get("pending_checkout") or {})
        if order and pending_checkout.get("order_public_id") == str(order.public_id):
            pending_checkout.update(
                {
                    "status": "COMPLETED",
                    "completed_at": timezone.now().isoformat(),
                }
            )

        locked_subscription.metadata = {
            **metadata,
            "pending_checkout": pending_checkout or metadata.get("pending_checkout"),
            "last_activated_payment_id": activation_key,
            "last_activated_at": timezone.now().isoformat(),
            "converted_from_trial_at": (
                timezone.now().isoformat()
                if was_trial
                else metadata.get("converted_from_trial_at")
            ),
            "previous_plan_id": previous_plan_id if is_plan_change else metadata.get("previous_plan_id"),
            "previous_billing_order_id": previous_order_id if is_plan_change else metadata.get("previous_billing_order_id"),
            "previous_gateway_subscription_id": (
                previous_gateway_subscription_id
                if is_plan_change
                else metadata.get("previous_gateway_subscription_id")
            ),
        }
        locked_subscription.save()

        if locked_payment.status not in {Payment.Status.CONFIRMED, Payment.Status.RECEIVED}:
            locked_payment.status = Payment.Status.CONFIRMED
            locked_payment.paid_at = paid_at
            locked_payment.confirmed_at = locked_payment.confirmed_at or paid_at
            locked_payment.save(update_fields=["status", "paid_at", "confirmed_at", "updated_at"])

        if order:
            order.status = BillingOrder.Status.PAID if order.installment_count == 1 else BillingOrder.Status.PARTIALLY_PAID
            order.confirmed_at = order.confirmed_at or paid_at
            order_metadata = dict(order.metadata or {})
            order_metadata["access_activated_at"] = order_metadata.get("access_activated_at") or timezone.now().isoformat()
            if is_plan_change:
                order_metadata["plan_change_completed_at"] = timezone.now().isoformat()
                order_metadata["previous_gateway_subscription_id"] = previous_gateway_subscription_id
                order_metadata["previous_subscription_cancel_pending"] = bool(
                    previous_gateway_subscription_id
                    and previous_gateway_subscription_id != order.gateway_subscription_id
                )
            order.metadata = order_metadata
            order.save(update_fields=["status", "confirmed_at", "metadata", "updated_at"])
        return locked_subscription

    @classmethod
    @transaction.atomic
    def mark_past_due(cls, subscription: Subscription) -> Subscription:
        locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if locked.status in {Subscription.Status.CANCELED, Subscription.Status.EXPIRED}:
            return locked
        grace_days = max(int(getattr(settings, "BILLING_GRACE_PERIOD_DAYS", 5)), 0)
        locked.status = Subscription.Status.PAST_DUE
        locked.grace_period_ends_at = timezone.now() + timedelta(days=grace_days)
        locked.save(update_fields=["status", "grace_period_ends_at", "updated_at"])
        return locked

    @classmethod
    @transaction.atomic
    def suspend_if_grace_expired(cls, subscription: Subscription) -> Subscription:
        locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if (
            locked.status == Subscription.Status.PAST_DUE
            and locked.grace_period_ends_at
            and locked.grace_period_ends_at < timezone.now()
        ):
            locked.status = Subscription.Status.SUSPENDED
            locked.suspended_at = timezone.now()
            locked.save(update_fields=["status", "suspended_at", "updated_at"])
        return locked

    @classmethod
    @transaction.atomic
    def schedule_cancellation(cls, subscription: Subscription) -> Subscription:
        locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if locked.status not in {Subscription.Status.ACTIVE, Subscription.Status.PAST_DUE}:
            raise ValidationError("A assinatura atual não permite cancelamento ao final do período.")
        locked.cancel_at_period_end = True
        locked.save(update_fields=["cancel_at_period_end", "updated_at"])
        return locked

    @classmethod
    @transaction.atomic
    def resume_cancellation(cls, subscription: Subscription) -> Subscription:
        locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
        locked.cancel_at_period_end = False
        locked.save(update_fields=["cancel_at_period_end", "updated_at"])
        return locked
