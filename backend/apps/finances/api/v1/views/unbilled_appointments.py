"""Endpoint de consultas ainda não cobradas."""

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.integrations.scheduling import unbilled_appointments_for


class UnbilledAppointmentActionsMixin:
    @action(detail=False, methods=["get"], url_path="unbilled-appointments")
    def unbilled_appointments(self, request):
        appointments = unbilled_appointments_for(actor=request.user)
        return Response(
            [
                {
                    "id": item.id,
                    "patient_id": item.patient_id,
                    "patient_name": item.patient.full_name,
                    "start_time": item.start_time,
                    "end_time": item.end_time,
                    "session_value": str(item.session_value or "0.00"),
                }
                for item in appointments
            ]
        )
