from django.utils import timezone
from rest_framework import serializers

from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, AppointmentRecurrence, Room
from apps.users.models import User


class AppointmentRecurrenceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)
    occurrences_count = serializers.IntegerField(source="appointments.count", read_only=True)
    completed_count = serializers.SerializerMethodField()
    next_occurrence_id = serializers.SerializerMethodField()
    next_occurrence_at = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentRecurrence
        fields = [
            "id", "patient", "patient_name", "therapist", "therapist_name", "frequency",
            "frequency_display", "interval", "weekdays", "starts_on", "ends_on",
            "max_occurrences", "start_time", "duration_minutes", "timezone_name", "modality",
            "appointment_type", "room", "session_value", "notes", "status",
            "occurrences_count", "completed_count", "next_occurrence_id", "next_occurrence_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        membership = getattr(request, "organization_membership", None)
        if organization is None:
            self.fields["patient"].queryset = Patient.objects.none()
            self.fields["therapist"].queryset = User.objects.none()
            self.fields["room"].queryset = Room.objects.none()
            return
        patients = Patient.objects.filter(organization=organization, is_active=True)
        therapist_ids = OrganizationMembership.objects.filter(
            organization=organization,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=[
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
                OrganizationMembership.Role.THERAPIST,
            ],
        ).values_list("user_id", flat=True)
        therapists = User.objects.filter(pk__in=therapist_ids, is_active=True)
        rooms = Room.objects.filter(organization=organization, is_active=True)
        if membership and membership.role == OrganizationMembership.Role.THERAPIST:
            patients = patients.filter(therapist=request.user)
            therapists = therapists.filter(pk=request.user.pk)
            rooms = rooms.filter(therapist=request.user)
        self.fields["patient"].queryset = patients
        self.fields["therapist"].queryset = therapists
        self.fields["room"].queryset = rooms

    def validate(self, attrs):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        membership = getattr(request, "organization_membership", None)
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        therapist = attrs.get("therapist", getattr(self.instance, "therapist", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        if membership and membership.role == OrganizationMembership.Role.THERAPIST:
            therapist = request.user
            attrs["therapist"] = therapist
        if organization is None:
            raise serializers.ValidationError({"organization": "Selecione uma organização."})
        if not patient or patient.organization_id != organization.pk:
            raise serializers.ValidationError({"patient": "O paciente pertence a outra organização."})
        if not therapist or patient.therapist_id != therapist.pk:
            raise serializers.ValidationError({"therapist": "O profissional não é responsável pelo paciente."})
        if room and room.organization_id != organization.pk:
            raise serializers.ValidationError({"room": "A sala pertence a outra organização."})
        starts_on = attrs.get("starts_on", getattr(self.instance, "starts_on", None))
        ends_on = attrs.get("ends_on", getattr(self.instance, "ends_on", None))
        if starts_on and ends_on and ends_on < starts_on:
            raise serializers.ValidationError({"ends_on": "A data final deve ser posterior à inicial."})
        return attrs

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].organization
        return super().create(validated_data)

    def get_completed_count(self, obj):
        return obj.appointments.filter(
            organization=obj.organization,
            status=Appointment.Status.COMPLETED,
        ).count()

    def _next(self, obj):
        return (
            obj.appointments.filter(
                organization=obj.organization,
                start_time__gte=timezone.now(),
                status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            )
            .order_by("start_time")
            .first()
        )

    def get_next_occurrence_id(self, obj):
        item = self._next(obj)
        return item.id if item else None

    def get_next_occurrence_at(self, obj):
        item = self._next(obj)
        return item.start_time if item else None
