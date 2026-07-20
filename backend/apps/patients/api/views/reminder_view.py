from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.patients.selectors.patients import patients_accessible_to


class PatientReminderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        user = request.user
        if not (user.is_admin_role or user.is_therapist):
            return Response(
                {"detail": "Acesso negado."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = patients_accessible_to(user)
        patient = get_object_or_404(queryset, pk=pk)

        enabled = request.data.get("enabled")
        if not isinstance(enabled, bool):
            return Response(
                {"enabled": "Informe true ou false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient.reminders_enabled = enabled
        patient.save(update_fields=["reminders_enabled", "updated_at"])
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=patient,
            obj_repr=f"Lembretes do paciente #{patient.pk}",
        )
        return Response({"reminders_enabled": enabled})
