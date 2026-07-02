from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .appointment_read import AppointmentDetailSerializer, AppointmentListSerializer
from .appointment_write import (
    AppointmentCreateSerializer as BaseAppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer as BaseAppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
)
from .availability import CheckAvailabilitySerializer, ScheduleBlockSerializer
from .packages import PatientPackageSerializer
from .recurrences import AppointmentRecurrenceSerializer
from .summary import (
    AppointmentReminderSerializer,
    PackageSessionSerializer,
    RoomSerializer,
    TelemedicineRoomSerializer,
)
from ..models import Appointment


class AppointmentCreateSerializer(BaseAppointmentCreateSerializer):
    """Adiciona isolamento do pacote e resposta detalhada após a criação."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        package = attrs.get("package")
        if package:
            patient = attrs.get("patient")
            therapist = attrs.get("therapist")
            if package.patient_id != patient.id or package.therapist_id != therapist.id:
                raise serializers.ValidationError(
                    {"package": "O pacote não pertence ao paciente e profissional selecionados."}
                )
            requested = (
                attrs.get("recurrence_max_occurrences", 1)
                if attrs.get("is_recurring")
                else 1
            )
            if package.remaining_sessions < requested:
                raise serializers.ValidationError(
                    {"package": "O pacote não possui saldo para todas as sessões solicitadas."}
                )
        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or getattr(
                exc, "messages", [str(exc)]
            )
            raise serializers.ValidationError(detail) from exc

    def to_representation(self, instance):
        return AppointmentDetailSerializer(instance, context=self.context).data


class AppointmentStatusUpdateSerializer(BaseAppointmentStatusUpdateSerializer):
    def validate(self, attrs):
        if self.instance.status == Appointment.Status.CANCELLED:
            raise serializers.ValidationError(
                {"status": "Uma consulta cancelada não pode ser reativada diretamente."}
            )
        return super().validate(attrs)


__all__ = [name for name in globals() if name.endswith("Serializer")]
