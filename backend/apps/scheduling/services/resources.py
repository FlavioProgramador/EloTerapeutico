"""Criação de recursos derivados de consultas."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.scheduling.models import Appointment, AppointmentReminder, PackageSession, PatientPackage, TelemedicineRoom


def mask_phone(value: str) -> str:
    digits = "".join(char for char in (value or "") if char.isdigit())
    return f"***{digits[-4:]}" if len(digits) >= 4 else "não informado"


def create_appointment_resources(
    appointment: Appointment,
    *,
    send_whatsapp_reminder: bool = False,
    package: PatientPackage | None = None,
) -> None:
    """Cria recursos derivados sem realizar envio externo na requisição."""
    if package:
        if package.patient_id != appointment.patient_id or package.therapist_id != appointment.therapist_id:
            raise ValidationError("O pacote não pertence ao paciente e profissional informados.")
        package.consume()
        PackageSession.objects.create(
            package=package,
            appointment=appointment,
            scheduled_for=appointment.start_time,
            status=PackageSession.Status.SCHEDULED,
            consumed=True,
        )

    if appointment.modality in {
        Appointment.Modality.ONLINE,
        Appointment.Modality.HYBRID,
    }:
        TelemedicineRoom.objects.get_or_create(
            appointment=appointment,
            defaults={
                "expires_at": appointment.end_time + timedelta(hours=2),
                "status": TelemedicineRoom.Status.AVAILABLE,
            },
        )

    if send_whatsapp_reminder:
        phone = appointment.patient.whatsapp or appointment.patient.phone
        AppointmentReminder.objects.create(
            appointment=appointment,
            channel=AppointmentReminder.Channel.WHATSAPP,
            scheduled_for=max(appointment.start_time - timedelta(hours=24), timezone.now()),
            recipient_masked=mask_phone(phone),
        )
