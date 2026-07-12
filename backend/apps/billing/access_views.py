from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.serializers import SubscriptionSerializer
from apps.billing.services.entitlements import get_entitlement


class EntitlementStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entitlement = get_entitlement(request.user)
        return Response(
            {
                "allowed": entitlement.allowed,
                "code": entitlement.code,
                "message": entitlement.message,
                "redirect_to": entitlement.redirect_to,
                "trial_days_remaining": entitlement.trial_days_remaining,
                "onboarding_required": entitlement.onboarding_required,
                "subscription": (
                    SubscriptionSerializer(entitlement.subscription).data
                    if entitlement.subscription
                    else None
                ),
            }
        )
