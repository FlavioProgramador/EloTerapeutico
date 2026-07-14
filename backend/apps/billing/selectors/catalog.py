from django.db.models import QuerySet

from apps.billing.models import Plan, PlanPrice


def get_active_plans() -> QuerySet[Plan]:
    return Plan.objects.filter(is_active=True).prefetch_related("prices").order_by("name")


def get_active_plan_prices(
    *,
    plan_slug: str | None = None,
    billing_interval: str | None = None,
    billing_model: str | None = None,
) -> QuerySet[PlanPrice]:
    queryset = PlanPrice.objects.select_related("plan").filter(
        is_active=True,
        plan__is_active=True,
    )
    if plan_slug:
        queryset = queryset.filter(plan__slug=plan_slug)
    if billing_interval:
        queryset = queryset.filter(billing_interval=billing_interval)
    if billing_model:
        queryset = queryset.filter(billing_model=billing_model)
    return queryset.order_by("plan__name", "billing_interval", "total_amount")
