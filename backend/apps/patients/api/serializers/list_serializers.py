from apps.patients.api.serializers.dashboard_serializers import PatientDashboardSerializer


class PatientReferenceListSerializer(PatientDashboardSerializer):
    """Campos administrativos seguros usados pela listagem principal."""

    class Meta(PatientDashboardSerializer.Meta):
        fields = [
            *PatientDashboardSerializer.Meta.fields,
            "birth_date",
            "reminders_enabled",
        ]
        read_only_fields = fields
