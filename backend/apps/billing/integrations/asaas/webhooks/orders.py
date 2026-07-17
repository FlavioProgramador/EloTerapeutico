from __future__ import annotations

from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from apps.billing.models import BillingOrder, Payment, PlanPrice, Subscription


def legacy_order_for_subscription(
    gateway_subscription_id: str | None,
) -> BillingOrder | None:
    if not gateway_subscription_id:
        return None
    subscription = (
        Subscription.objects.select_related("plan", "billing_order")
        .filter(gateway_subscription_id=gateway_subscription_id)
        .first()
    )
    if not subscription:
        return None
    if subscription.billing_order_id:
        return subscription.billing_order

    plan = subscription.plan
    interval = (
        PlanPrice.BillingInterval.YEARLY
        if plan.billing_cycle == "YEARLY"
        else PlanPrice.BillingInterval.MONTHLY
    )
    price, _ = PlanPrice.objects.get_or_create(
        slug=f"{plan.slug}-{interval.lower()}-recurring-webhook-legacy",
        defaults={
            "plan": plan,
            "name": (
                f"{plan.name} — "
                f"{'Anual' if interval == 'YEARLY' else 'Mensal'}"
            ),
            "currency": plan.currency,
            "total_amount": plan.price,
            "billing_interval": interval,
            "billing_model": PlanPrice.BillingModel.RECURRING,
            "discount_percentage": Decimal("0.00"),
            "installments_enabled": False,
            "min_installments": 1,
            "max_installments": 1,
            "is_active": plan.is_active,
        },
    )
    external_reference = f"legacy-webhook-subscription-{subscription.pk}"
    order, _ = BillingOrder.objects.get_or_create(
        external_reference=external_reference,
        defaults={
            "user": subscription.user,
            "plan": plan,
            "plan_price": price,
            "status": BillingOrder.Status.PENDING,
            "billing_model": price.billing_model,
            "billing_interval": price.billing_interval,
            "currency": price.currency,
            "total_amount": price.total_amount,
            "discount_amount": Decimal("0.00"),
            "installment_count": 1,
            "installment_amount_estimate": price.total_amount,
            "gateway_name": subscription.gateway_name,
            "gateway_customer_id": subscription.gateway_customer_id,
            "gateway_subscription_id": gateway_subscription_id,
            "idempotency_key": external_reference,
            "commercial_snapshot": {
                "legacy": True,
                "plan_name": plan.name,
                "total_amount": str(price.total_amount),
            },
            "metadata": {"origin": "legacy_webhook_compatibility"},
        },
    )
    if not subscription.billing_order_id:
        subscription.billing_order = order
        subscription.save(update_fields=["billing_order", "updated_at"])
    Payment.objects.filter(
        subscription=subscription,
        billing_order__isnull=True,
    ).update(billing_order=order)
    return order


def find_order(payment_data: dict) -> BillingOrder | None:
    payment_id = payment_data.get("id")
    if payment_id:
        existing = (
            Payment.objects.select_related("billing_order")
            .filter(gateway_payment_id=payment_id)
            .first()
        )
        if existing and existing.billing_order_id:
            return existing.billing_order

    gateway_subscription_id = payment_data.get("subscription")
    query = Q()
    if gateway_subscription_id:
        query |= Q(gateway_subscription_id=gateway_subscription_id)
    if payment_data.get("installment"):
        query |= Q(gateway_installment_id=payment_data["installment"])
    if payment_data.get("externalReference"):
        query |= Q(external_reference=payment_data["externalReference"])

    order = None
    if query:
        order = (
            BillingOrder.objects.select_related("plan", "plan_price", "user")
            .filter(query)
            .order_by("-created_at")
            .first()
        )
    return order or legacy_order_for_subscription(gateway_subscription_id)


def subscription_for_order(
    order: BillingOrder,
    payment_data: dict,
) -> Subscription | None:
    subscription = (
        Subscription.objects.filter(billing_order=order)
        .order_by("-created_at")
        .first()
    )
    if subscription:
        return subscription
    gateway_subscription_id = payment_data.get("subscription")
    if gateway_subscription_id:
        return Subscription.objects.filter(
            gateway_subscription_id=gateway_subscription_id
        ).first()
    source_id = (order.metadata or {}).get(
        "plan_change_from_subscription_id"
    )
    return Subscription.objects.filter(pk=source_id).first() if source_id else None


def update_order_financial_status(order: BillingOrder) -> None:
    payments = Payment.objects.filter(billing_order=order)
    total = payments.count()
    paid = payments.filter(
        status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED]
    ).count()
    overdue = payments.filter(status=Payment.Status.OVERDUE).exists()
    chargeback = payments.filter(status=Payment.Status.CHARGEBACK).exists()
    refunded = payments.filter(status=Payment.Status.REFUNDED).count()

    if chargeback:
        next_status = BillingOrder.Status.CHARGEBACK
    elif total and refunded == total:
        next_status = BillingOrder.Status.REFUNDED
    elif refunded:
        next_status = BillingOrder.Status.PARTIALLY_REFUNDED
    elif total and paid == total:
        next_status = BillingOrder.Status.PAID
    elif paid:
        next_status = BillingOrder.Status.PARTIALLY_PAID
    elif overdue:
        next_status = BillingOrder.Status.OVERDUE
    else:
        next_status = BillingOrder.Status.PENDING

    if order.status != next_status:
        order.status = next_status
        update_fields = ["status", "updated_at"]
        if (
            next_status
            in {
                BillingOrder.Status.PAID,
                BillingOrder.Status.PARTIALLY_PAID,
            }
            and not order.confirmed_at
        ):
            order.confirmed_at = timezone.now()
            update_fields.append("confirmed_at")
        order.save(update_fields=update_fields)
