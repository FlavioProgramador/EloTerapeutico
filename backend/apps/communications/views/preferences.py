from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.organizations.services.tenant_context import ensure_request_organization
from apps.patients.selectors.patients import patients_accessible_to

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

    def get_context(self, request):
        organization, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        return organization, membership

    def get_organization(self, request):
        organization, _ = self.get_context(request)
        return organization


class CommunicationPreferenceListView(CommunicationPreferenceMixin, APIView):
    def get(self, request):
        organization, membership = self.get_context(request)
        accessible_patients = patients_accessible_to(
            request.user,
            organization=organization,
            membership=membership,
        )
        queryset = CommunicationPreference.objects.filter(
            organization=organization,
            patient__in=accessible_patients,
        ).select_related("organization", "patient", "owner")
        return Response(
            CommunicationPreferenceSerializer(queryset, many=True).data
        )


class PatientCommunicationPreferenceView(CommunicationPreferenceMixin, APIView):
    def get_preference(self, request, patient_id):
        organization, membership = self.get_context(request)
        patient = get_object_or_404(
            patients_accessible_to(
                request.user,
                organization=organization,
                membership=membership,
            ),
            pk=patient_id,
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
