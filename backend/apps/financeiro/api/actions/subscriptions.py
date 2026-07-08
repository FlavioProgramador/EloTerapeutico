"""Actions de mensalidades expostas pelo ViewSet financeiro."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ...models import MonthlySubscription
from ...serializers import MonthlySubscriptionSerializer


class SubscriptionActions:
    def _subscriptions_for_user(self, user):
        queryset = MonthlySubscription.objects.select_related("patient", "therapist")
        if user.is_admin_role or user.is_secretary:
            return queryset
        return queryset.filter(therapist=user)

    @action(detail=False, methods=["get", "post"], url_path="subscriptions")
    def subscriptions(self, request):
        if request.method == "GET":
            queryset = self._subscriptions_for_user(request.user)
            selected_status = request.query_params.get("status")
            if selected_status:
                queryset = queryset.filter(status=selected_status)
            serializer = MonthlySubscriptionSerializer(queryset, many=True)
            return Response(serializer.data)

        serializer = MonthlySubscriptionSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        url_path=r"subscriptions/(?P<subscription_id>[^/.]+)/status",
    )
    def subscription_status(self, request, subscription_id=None):
        subscription = get_object_or_404(
            self._subscriptions_for_user(request.user),
            pk=subscription_id,
        )
        target = request.data.get("status")
        allowed = {choice for choice, _ in MonthlySubscription.Status.choices}
        if target not in allowed:
            return Response(
                {"detail": "Status de mensalidade inválido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.status = target
        subscription.save(update_fields=["status", "updated_at"])
        return Response(MonthlySubscriptionSerializer(subscription).data)
