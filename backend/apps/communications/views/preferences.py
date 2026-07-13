from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.patients.models import Patient

from ..models import CommunicationPreference
from ..permissions import CanAccessCommunications
from ..serializers import CommunicationPreferenceSerializer
from ..services import get_or_create_preference
from .common import _audit


class CommunicationPreferenceListView(APIView):
    permission_classes = [IsAuthenticated, CanAccessCommunications]

    def get(self, request):
        queryset = CommunicationPreference.objects.filter(owner=request.user).select_related("patient")
        return Response(CommunicationPreferenceSerializer(queryset, many=True).data)


class PatientCommunicationPreferenceView(APIView):
    permission_classes = [IsAuthenticated, CanAccessCommunications]

    def get_preference(self, request, patient_id):
        patient = get_object_or_404(Patient, pk=patient_id, therapist=request.user)
        return get_or_create_preference(request.user, patient)

    def get(self, request, patient_id):
        return Response(CommunicationPreferenceSerializer(self.get_preference(request, patient_id)).data)

    def patch(self, request, patient_id):
        preference = self.get_preference(request, patient_id)
        serializer = CommunicationPreferenceSerializer(preference, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        preference = serializer.save()
        _audit(request, AuditLog.Action.UPDATE, preference, "communication_preference_updated")
        return Response(CommunicationPreferenceSerializer(preference).data)
