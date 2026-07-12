from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.agenda.models import Appointment, Room, ScheduleBlock
from apps.patients.models import Patient
from apps.users.models import WorkingHours


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
                        "Existem consultas no intervalo. Confirme para criar o " "bloqueio sem cancelá-las."
                    )
                }
            )
        attrs.pop("confirm_conflicts", None)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        recurrence_count = validated_data.pop("recurrence_count", 4)
        validated_data["created_by"] = self.context["request"].user
        item = super().create(validated_data)
        delta = {
            "weekly": timedelta(weeks=1),
            "biweekly": timedelta(weeks=2),
        }.get(item.recurrence_rule)
        if delta:
            for index in range(1, recurrence_count):
                ScheduleBlock.objects.create(
                    therapist=item.therapist,
                    start_time=item.start_time + delta * index,
                    end_time=item.end_time + delta * index,
                    reason=item.reason,
                    notes=item.notes,
                    recurrence_rule=item.recurrence_rule,
                    parent_block=item,
                    created_by=item.created_by,
                )
        return item


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
        target_date = validated_data["date"]
        duration = validated_data["duration"]
        working = WorkingHours.objects.filter(
            therapist=therapist,
            weekday=target_date.weekday(),
            is_active=True,
        ).first()
        if not working:
            return []
        tz = timezone.get_current_timezone()
        current = timezone.make_aware(datetime.combine(target_date, working.start_time), tz)
        day_end = timezone.make_aware(datetime.combine(target_date, working.end_time), tz)
        patient = Patient.objects.filter(pk=validated_data.get("patient_id")).first()
        room = Room.objects.filter(pk=validated_data.get("room_id"), is_active=True).first()
        slots = []
        while current + timedelta(minutes=duration) <= day_end:
            end = current + timedelta(minutes=duration)
            conflicts = Appointment.conflict_details(
                therapist=therapist,
                patient=patient,
                start_time=current,
                end_time=end,
                room=room,
            )
            if (
                not conflicts["therapist"]
                and not conflicts["room"]
                and not conflicts["block"]
                and (not patient or not conflicts["patient"])
            ):
                slots.append(
                    {
                        "start": current.strftime("%H:%M"),
                        "end": end.strftime("%H:%M"),
                        "start_datetime": current.isoformat(),
                        "end_datetime": end.isoformat(),
                    }
                )
            current = end
        return slots
