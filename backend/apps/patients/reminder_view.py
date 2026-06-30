from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient


class PatientReminderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        user = request.user
        if not (user.is_admin_role or user.is_therapist):
            return Response({"detail": "Acesso negado."}, status=status.HTTP_403_FORBIDDEN)
        queryset = Patient.objects.all()
        if user.is_therapist:
            queryset = queryset.filter(therapist=user)
        patient = get_object_or_404(queryset, pk=pk)
        enabled = request.data.get("enabled")
        if not isinstance(enabled, bool):
            return Response({"enabled": "Informe true ou false."}, status=status.HTTP_400_BAD_REQUEST)
        patient.reminders_enabled = enabled
        patient.save(update_fields=["reminders_enabled", "updated_at"])
        return Response({"reminders_enabled": enabled})
