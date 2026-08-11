"""Serializers de geração de cobranças por consulta."""

from rest_framework import serializers


class AppointmentChargeGenerationSerializer(serializers.Serializer):
    appointment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )
    due_date = serializers.DateField()

    def validate_appointment_ids(self, values):
        if len(values) != len(set(values)):
            raise serializers.ValidationError(
                "Não repita consultas na mesma solicitação."
            )
        return values
