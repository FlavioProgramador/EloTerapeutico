from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Payment, Plan
from apps.billing.serializers import (
    ChangePlanSerializer,
    CreateSubscriptionSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from apps.billing.services.subscriptions import (
    cancel_subscription,
    change_plan,
    create_subscription_for_user,
    get_current_subscription,
)
from apps.billing.webhooks.asaas import handle_asaas_webhook


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by("price", "name")


class CurrentSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = get_current_subscription(request.user)
        if not subscription:
            return Response({"subscription": None})
        return Response({"subscription": SubscriptionSerializer(subscription).data})


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = create_subscription_for_user(request.user, serializer.validated_data["plan"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = cancel_subscription(request.user)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(subscription).data)


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = change_plan(request.user, serializer.validated_data["plan"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-due_date", "-created_at")


class AsaasWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            event = handle_asaas_webhook(request)
        except PermissionDenied:
            return Response({"detail": "Webhook inválido."}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "received": True,
                "processed": event.processed,
                "event_type": event.event_type,
            },
            status=status.HTTP_200_OK,
        )
