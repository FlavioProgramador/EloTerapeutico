from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.services.tenant_context import ensure_request_organization

from ..permissions import CanAccessCommunications, CanViewCommunicationLogs
from ..selectors import communication_dashboard
from .common import _parse_period


class CommunicationDashboardView(APIView):
    permission_classes = [
        IsAuthenticated,
        CanAccessCommunications,
        CanViewCommunicationLogs,
    ]

    def get(self, request):
        organization, _ = ensure_request_organization(
            request=request,
            required=True,
        )
        start, end = _parse_period(request)
        return Response(
            communication_dashboard(
                request.user,
                start,
                end,
                organization=organization,
            )
        )
