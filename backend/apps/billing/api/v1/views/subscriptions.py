from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.v1.serializers import (
    ChangePlanSerializer,
    CreateSubscriptionSerializer,
    SubscriptionSerializer,
)
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.subscriptions import (
    cancel_subscription,
    change_plan,
    create_subscription_for_user,
    get_current_subscription,
    resume_subscription_cancellation,
    schedule_subscription_cancellation,
)

from .common import gateway_error_response, validation_error_response


class CurrentSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = get_current_subscription(request.user)
        if not subscription:
            return Response({"subscription": None})
        return Response(
            {"subscription": SubscriptionSerializer(subscription).data}
        )


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = create_subscription_for_user(
                request.user,
                serializer.validated_data["plan"],
            )
        except DjangoValidationError:
            return validation_error_response()
        except GatewayError:
            return gateway_error_response("subscription_create")
        return Response(
            SubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = cancel_subscription(request.user)
        except DjangoValidationError:
            return validation_error_response()
        except GatewayError:
            return gateway_error_response("subscription_cancel")
        return Response(SubscriptionSerializer(subscription).data)


class ScheduleCancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = schedule_subscription_cancellation(request.user)
        except DjangoValidationError:
            return validation_error_response()
        return Response(SubscriptionSerializer(subscription).data)


class ResumeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = resume_subscription_cancellation(request.user)
        except DjangoValidationError:
            return validation_error_response()
        return Response(SubscriptionSerializer(subscription).data)


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = change_plan(
                request.user,
                serializer.validated_data["plan"],
            )
        except DjangoValidationError:
            return validation_error_response()
        return Response(
            {
                "subscription": SubscriptionSerializer(subscription).data,
                "detail": (
                    "Troca registrada. Conclua o checkout do novo preço "
                    "para efetivar a alteração."
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )
