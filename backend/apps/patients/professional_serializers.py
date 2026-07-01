from rest_framework import serializers

from apps.users.models import User


class PatientProfessionalOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "specialty"]
        read_only_fields = fields
