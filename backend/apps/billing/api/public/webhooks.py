from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.webhooks.asaas import handle_asaas_webhook


class AsaasWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            event = handle_asaas_webhook(request)
        except PermissionDenied:
            return Response(
                {"detail": "Webhook inválido."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {
                "received": True,
                "processed": event.processed,
                "status": event.status,
                "event_type": event.event_type,
            },
            status=status.HTTP_200_OK,
        )
