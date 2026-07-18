from django.utils import timezone
from rest_framework import serializers

from apps.scheduling.models import Appointment, ScheduleBlock
from apps.scheduling.selectors import available_slots
from apps.scheduling.services import create_schedule_block


class ScheduleBlockSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    affected_appointments = serializers.SerializerMethodField(read_only=True)
    confirm_conflicts = serializers.BooleanField(write_only=True, required=False, default=False)
    recurrence_count = serializers.IntegerField(write_only=True, required=False, default=4, min_value=2, max_value=52)

    class Meta:
        model = ScheduleBlock
        fields = [
            "id",
            "therapist",
            "therapist_name",
            "start_time",
            "end_time",
            "reason",
            "notes",
            "is_active",
            "recurrence_rule",
            "parent_block",
            "affected_appointments",
            "confirm_conflicts",
            "recurrence_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["parent_block", "created_at", "updated_at"]

    def get_affected_appointments(self, obj):
        return (
            Appointment.active_queryset()
            .filter(
                therapist=obj.therapist,
                start_time__lt=obj.end_time,
                end_time__gt=obj.start_time,
            )
            .count()
        )

    def validate(self, attrs):
        request = self.context["request"]
        therapist = attrs.get("therapist", getattr(self.instance, "therapist", None))
        if request.user.is_therapist:
            therapist = request.user
            attrs["therapist"] = therapist
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and start >= end:
            raise serializers.ValidationError({"end_time": "O término deve ser posterior ao início."})
        overlap = ScheduleBlock.objects.filter(
            therapist=therapist,
            is_active=True,
            start_time__lt=end,
            end_time__gt=start,
        )
        if self.instance:
            overlap = overlap.exclude(pk=self.instance.pk)
        if overlap.exists():
            raise serializers.ValidationError({"start_time": "Já existe um bloqueio nesse intervalo."})
        affected = (
            Appointment.active_queryset()
            .filter(
                therapist=therapist,
                start_time__lt=end,
                end_time__gt=start,
            )
            .exists()
        )
        if affected and not attrs.pop("confirm_conflicts", False):
            raise serializers.ValidationError(
                {
                    "confirm_conflicts": (
                        "Existem consultas no intervalo. Confirme para criar o bloqueio sem cancelá-las."
                    )
                }
            )
        attrs.pop("confirm_conflicts", None)
        return attrs

    def create(self, validated_data):
        return create_schedule_block(
            actor=self.context["request"].user,
            validated_data=validated_data,
        )


class CheckAvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField()
    duration = serializers.IntegerField(default=50, min_value=15, max_value=240)
    therapist_id = serializers.IntegerField(required=False)
    room_id = serializers.IntegerField(required=False)
    patient_id = serializers.IntegerField(required=False)

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Não é possível consultar disponibilidade no passado.")
        return value

    def get_available_slots(self, therapist, validated_data):
        return available_slots(
            therapist=therapist,
            target_date=validated_data["date"],
            duration=validated_data["duration"],
            patient_id=validated_data.get("patient_id"),
            room_id=validated_data.get("room_id"),
        )
