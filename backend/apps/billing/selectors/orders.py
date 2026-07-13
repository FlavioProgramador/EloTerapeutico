from django.db.models import QuerySet

from apps.billing.models import BillingOrder


def get_orders_for_user(*, user) -> QuerySet[BillingOrder]:
    return (
        BillingOrder.objects.filter(user_id=user.pk)
        .select_related("plan", "plan_price")
        .prefetch_related("payments")
        .order_by("-created_at")
    )


def get_order_with_payments(*, order_id: int) -> BillingOrder:
    return (
        BillingOrder.objects.select_related("plan", "plan_price")
        .prefetch_related("payments")
        .get(pk=order_id)
    )
