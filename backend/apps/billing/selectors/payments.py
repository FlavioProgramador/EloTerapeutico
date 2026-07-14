from decimal import Decimal
from typing import Any

from django.db.models import QuerySet, Sum

from apps.billing.models import Payment

ALLOWED_PAYMENT_ORDERING = {
    "due_date",
    "-due_date",
    "created_at",
    "-created_at",
    "status",
    "-status",
}


def get_payments_for_user(
    *,
    user,
    payment_status: str | None = None,
    order_public_id: str | None = None,
    ordering: str = "due_date",
) -> QuerySet[Payment]:
    queryset = Payment.objects.filter(user_id=user.pk).select_related(
        "billing_order",
        "subscription",
    )
    if payment_status:
        queryset = queryset.filter(status=payment_status)
    if order_public_id:
        queryset = queryset.filter(billing_order__public_id=order_public_id)
    normalized_ordering = ordering if ordering in ALLOWED_PAYMENT_ORDERING else "due_date"
    return queryset.order_by(normalized_ordering, "installment_number")


def get_payment_for_refresh(*, user, payment_id: int) -> Payment | None:
    return (
        Payment.objects.select_related("billing_order", "subscription")
        .filter(pk=payment_id, user_id=user.pk)
        .first()
    )


def get_payment_summary(*, user, order_public_id: str | None = None) -> dict[str, Any]:
    queryset = Payment.objects.filter(user_id=user.pk)
    if order_public_id:
        queryset = queryset.filter(billing_order__public_id=order_public_id)

    paid = queryset.filter(status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED])
    pending = queryset.filter(status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE])
    total = queryset.aggregate(value=Sum("amount"))["value"] or Decimal("0.00")
    paid_total = paid.aggregate(value=Sum("amount"))["value"] or Decimal("0.00")
    next_payment = pending.order_by("due_date").first()

    return {
        "total_amount": str(total),
        "paid_amount": str(paid_total),
        "paid_installments": paid.count(),
        "total_installments": queryset.count(),
        "next_due_date": next_payment.due_date if next_payment else None,
        "overdue_installments": queryset.filter(status=Payment.Status.OVERDUE).count(),
    }
