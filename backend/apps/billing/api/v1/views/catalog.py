from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.billing.api.v1.serializers import PlanPriceSerializer, PlanSerializer
from apps.billing.selectors.catalog import get_active_plan_prices, get_active_plans


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_active_plans()


class PlanPriceListView(generics.ListAPIView):
    serializer_class = PlanPriceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_active_plan_prices(
            plan_slug=self.request.query_params.get("plan"),
            billing_interval=self.request.query_params.get("billing_interval"),
            billing_model=self.request.query_params.get("billing_model"),
        )
