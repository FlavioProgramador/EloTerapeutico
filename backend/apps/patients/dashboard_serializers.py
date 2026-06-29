from rest_framework import serializers

from .models import Patient


class PatientDashboardSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    masked_cpf = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "masked_cpf",
            "age",
            "phone",
            "email",
            "status",
            "status_display",
        ]
