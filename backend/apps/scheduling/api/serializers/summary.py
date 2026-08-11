from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.models import AppointmentReminder, PackageSession, Room, TelemedicineRoom

User = get_user_model()


class PatientSummarySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    masked_cpf = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "display_name", "full_name", "masked_cpf", "phone", "whatsapp"]


class TherapistSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "specialty"]


class RoomSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "therapist", "therapist_name", "name", "location", "capacity",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        membership = getattr(request, "organization_membership", None)
        if organization is None:
            self.fields["therapist"].queryset = User.objects.none()
            return
        therapist_ids = OrganizationMembership.objects.filter(
            organization=organization,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=[
                OrganizationMembership.Role.OWNER,
                OrganizationMembership.Role.ADMIN,
                OrganizationMembership.Role.THERAPIST,
            ],
        ).values_list("user_id", flat=True)
        queryset = User.objects.filter(pk__in=therapist_ids, is_active=True)
        if membership and membership.role == OrganizationMembership.Role.THERAPIST:
            queryset = queryset.filter(pk=request.user.pk)
        self.fields["therapist"].queryset = queryset

    def validate_therapist(self, value):
        request = self.context["request"]
        organization = getattr(request, "organization", None)
        membership = getattr(request, "organization_membership", None)
        if organization is None:
            raise serializers.ValidationError("Selecione uma organização.")
        if membership and membership.role == OrganizationMembership.Role.THERAPIST and value != request.user:
            raise serializers.ValidationError("Você só pode gerenciar suas próprias salas.")
        if not OrganizationMembership.objects.filter(
            organization=organization,
            user=value,
            status=OrganizationMembership.Status.ACTIVE,
        ).exists():
            raise serializers.ValidationError("O responsável não pertence à organização.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        membership = getattr(request, "organization_membership", None)
        if membership and membership.role == OrganizationMembership.Role.THERAPIST:
            validated_data["therapist"] = request.user
        validated_data["organization"] = request.organization
        return super().create(validated_data)


class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = [
            "id", "appointment", "channel", "scheduled_for", "status",
            "recipient_masked", "error_message", "sent_at", "created_at",
        ]
        read_only_fields = fields


class TelemedicineRoomSerializer(serializers.ModelSerializer):
    patient_link = serializers.SerializerMethodField()
    professional_link = serializers.SerializerMethodField()
    is_accessible = serializers.BooleanField(read_only=True)
    appointment_start = serializers.DateTimeField(source="appointment.start_time", read_only=True)
    patient_name = serializers.CharField(source="appointment.patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="appointment.therapist.full_name", read_only=True)

    class Meta:
        model = TelemedicineRoom
        fields = [
            "id", "appointment", "appointment_start", "patient_name", "therapist_name",
            "patient_link", "professional_link", "expires_at", "status", "is_accessible",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def _build_link(self, role: str, token) -> str:
        base = settings.FRONTEND_URL.rstrip("/")
        return f"{base}/consulta-online/{role}/{token}"

    def get_patient_link(self, obj):
        return self._build_link("patient", obj.patient_token)

    def get_professional_link(self, obj):
        return self._build_link("professional", obj.professional_token)


class PackageSessionSerializer(serializers.ModelSerializer):
    appointment_status = serializers.CharField(source="appointment.status", read_only=True)

    class Meta:
        model = PackageSession
        fields = [
            "id", "package", "appointment", "appointment_status", "scheduled_for",
            "status", "consumed", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is not None:
            self.fields["package"].queryset = self.fields["package"].queryset.filter(
                organization=organization
            )
            self.fields["appointment"].queryset = self.fields["appointment"].queryset.filter(
                organization=organization
            )
        else:
            self.fields["package"].queryset = self.fields["package"].queryset.none()
            self.fields["appointment"].queryset = self.fields["appointment"].queryset.none()

    def create(self, validated_data):
        validated_data["organization"] = self.context["request"].organization
        return super().create(validated_data)
