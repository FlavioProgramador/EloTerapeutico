from rest_framework import serializers

from apps.forms.models import TherapeuticForm
from apps.forms.services import create_form, update_form

from .fields import FormFieldSerializer, validate_field_payload


class TherapeuticFormSerializer(serializers.ModelSerializer):
    fields = FormFieldSerializer(many=True)
    fields_count = serializers.IntegerField(source="fields.count", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
    )
    updated_by_name = serializers.CharField(
        source="updated_by.full_name",
        read_only=True,
    )

    class Meta:
        model = TherapeuticForm
        fields = (
            "id",
            "name",
            "description",
            "category",
            "category_display",
            "status",
            "status_display",
            "source_template",
            "fields_count",
            "fields",
            "created_by_name",
            "updated_by_name",
            "archived_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status_display",
            "category_display",
            "source_template",
            "fields_count",
            "created_by_name",
            "updated_by_name",
            "archived_at",
            "created_at",
            "updated_at",
        )

    def _organization(self):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is None:
            raise serializers.ValidationError(
                {"organization": "Selecione uma organização."}
            )
        return organization

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do formulário.")
        return value

    def validate_fields(self, fields):
        if not fields:
            raise serializers.ValidationError(
                "Adicione ao menos um campo ao formulário."
            )
        for index, field in enumerate(fields, start=1):
            field["order"] = field.get("order") or index
            validate_field_payload(field)
        return fields

    def create(self, validated_data):
        request = self.context["request"]
        return create_form(
            actor=request.user,
            organization=self._organization(),
            validated_data=validated_data,
        )

    def update(self, instance, validated_data):
        request = self.context["request"]
        return update_form(
            actor=request.user,
            organization=self._organization(),
            form=instance,
            validated_data=validated_data,
        )
