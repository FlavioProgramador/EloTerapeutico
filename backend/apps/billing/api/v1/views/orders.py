from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.billing.api.v1.serializers import BillingOrderSerializer
from apps.billing.selectors.orders import get_orders_for_user


class BillingOrderListView(generics.ListAPIView):
    serializer_class = BillingOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_orders_for_user(user=self.request.user)


class BillingOrderDetailView(generics.RetrieveAPIView):
    serializer_class = BillingOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def get_queryset(self):
        return get_orders_for_user(user=self.request.user)
