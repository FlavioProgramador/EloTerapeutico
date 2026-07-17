from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.services.integration_health import get_billing_integration_health


class BillingIntegrationHealthView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        payload = get_billing_integration_health()
        return Response(
            payload,
            status=(
                status.HTTP_200_OK
                if payload["connected"]
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )
