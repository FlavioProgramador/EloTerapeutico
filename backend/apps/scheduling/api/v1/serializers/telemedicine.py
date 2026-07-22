"""Contratos seguros de telemedicina da API v1."""

from rest_framework import serializers

from apps.scheduling.models import TelemedicineInvitation, TelemedicineRoom


class TelemedicineRoomSerializer(serializers.ModelSerializer):
    appointment_start = serializers.DateTimeField(
        source="appointment.start_time",
        read_only=True,
    )
    appointment_end = serializers.DateTimeField(
        source="appointment.end_time",
        read_only=True,
    )
    modality = serializers.CharField(source="appointment.modality", read_only=True)
    patient_name = serializers.CharField(
        source="appointment.patient.display_name",
        read_only=True,
    )
    therapist_name = serializers.CharField(
        source="appointment.therapist.full_name",
        read_only=True,
    )
    is_accessible = serializers.BooleanField(read_only=True)
    invitation_status = serializers.SerializerMethodField()
    active_participants = serializers.SerializerMethodField()

    class Meta:
        model = TelemedicineRoom
        fields = [
            "id",
            "public_id",
            "appointment",
            "appointment_start",
            "appointment_end",
            "modality",
            "patient_name",
            "therapist_name",
            "expires_at",
            "status",
            "is_accessible",
            "e2ee_enabled",
            "started_at",
            "ended_at",
            "patient_joined_at",
            "professional_joined_at",
            "last_participant_left_at",
            "invitation_status",
            "active_participants",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_invitation_status(self, obj):
        invitation = next(
            (
                item
                for item in obj.invitations.all()
                if item.role == TelemedicineInvitation.Role.PATIENT
                and item.revoked_at is None
            ),
            None,
        )
        if invitation is None:
            return {"status": "missing", "expires_at": None, "last_used_at": None}
        return {
            "status": "valid" if invitation.is_valid else "expired",
            "expires_at": invitation.expires_at,
            "last_used_at": invitation.last_used_at,
        }

    def get_active_participants(self, obj):
        return list(
            obj.participant_sessions.filter(left_at__isnull=True).values(
                "role",
                "provider_participant_identity",
                "joined_at",
            )
        )


class TelemedicineInvitationTokenSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=512, trim_whitespace=True)


class TelemedicineConsentSerializer(TelemedicineInvitationTokenSerializer):
    accepted = serializers.BooleanField()
    responsible_guardian_name = serializers.CharField(
        max_length=180,
        required=False,
        allow_blank=True,
        default="",
    )


class TelemedicineParticipantRemovalSerializer(serializers.Serializer):
    identity = serializers.CharField(min_length=16, max_length=180)


class TelemedicinePublicLeaveSerializer(TelemedicineInvitationTokenSerializer):
    identity = serializers.CharField(min_length=16, max_length=180)
