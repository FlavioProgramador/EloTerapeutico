"""Endpoints de mensalidades recorrentes."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import (
    MonthlySubscriptionSerializer,
    MonthlySubscriptionStatusSerializer,
)
from apps.finances.selectors import monthly_subscriptions_accessible_to
from apps.finances.services import (
    change_monthly_subscription_status,
    create_monthly_subscription,
)
from apps.organizations.services.tenant_context import ensure_request_organization


class MonthlySubscriptionActionsMixin:
    def _financial_organization(self):
        organization, _ = ensure_request_organization(
            request=self.request,
            required=True,
        )
        return organization

    @action(detail=False, methods=["get", "post"], url_path="subscriptions")
    def subscriptions(self, request):
        organization = self._financial_organization()
        if request.method == "GET":
            queryset = monthly_subscriptions_accessible_to(
                request.user,
                organization=organization,
                status=request.query_params.get("status"),
            )
            return Response(
                MonthlySubscriptionSerializer(queryset, many=True).data
            )
        serializer = MonthlySubscriptionSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        instance = create_monthly_subscription(
            actor=request.user,
            organization=organization,
            validated_data=serializer.validated_data,
        )
        return Response(
            MonthlySubscriptionSerializer(
                instance,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path=r"subscriptions/(?P<subscription_id>[^/.]+)/status",
    )
    def subscription_status(self, request, subscription_id=None):
        organization = self._financial_organization()
        current = get_object_or_404(
            monthly_subscriptions_accessible_to(
                request.user,
                organization=organization,
            ),
            pk=subscription_id,
        )
        serializer = MonthlySubscriptionStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current = change_monthly_subscription_status(
            actor=request.user,
            organization=organization,
            monthly_subscription=current,
            target_status=serializer.validated_data["status"],
        )
        return Response(MonthlySubscriptionSerializer(current).data)
