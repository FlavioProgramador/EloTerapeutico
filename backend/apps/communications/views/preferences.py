from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.organizations.services.tenant_context import ensure_request_organization
from apps.patients.models import Patient

from ..models import CommunicationPreference
from ..permissions import CanAccessCommunications, CanSendCommunication
from ..serializers import CommunicationPreferenceSerializer
from ..services import get_or_create_preference
from .common import _audit


class CommunicationPreferenceMixin:
    permission_classes = [
        IsAuthenticated,
        CanAccessCommunications,
        CanSendCommunication,
    ]

    def get_organization(self, request):
        organization, _ = ensure_request_organization(
            request=request,
            required=True,
        )
        return organization


class CommunicationPreferenceListView(CommunicationPreferenceMixin, APIView):
    def get(self, request):
        queryset = CommunicationPreference.objects.filter(
            organization=self.get_organization(request),
        ).select_related("organization", "patient", "owner")
        return Response(
            CommunicationPreferenceSerializer(queryset, many=True).data
        )


class PatientCommunicationPreferenceView(CommunicationPreferenceMixin, APIView):
    def get_preference(self, request, patient_id):
        organization = self.get_organization(request)
        patient = get_object_or_404(
            Patient,
            pk=patient_id,
            organization=organization,
            deleted_at__isnull=True,
        )
        return get_or_create_preference(
            request.user,
            patient,
            organization=organization,
        )

    def get(self, request, patient_id):
        return Response(
            CommunicationPreferenceSerializer(
                self.get_preference(request, patient_id)
            ).data
        )

    def patch(self, request, patient_id):
        preference = self.get_preference(request, patient_id)
        serializer = CommunicationPreferenceSerializer(
            preference,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        preference = serializer.save()
        _audit(
            request,
            AuditLog.Action.UPDATE,
            preference,
            "communication_preference_updated",
        )
        return Response(CommunicationPreferenceSerializer(preference).data)
