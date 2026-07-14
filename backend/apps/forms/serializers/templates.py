from rest_framework import serializers

from apps.forms.models import FormTemplate


class FormTemplateSerializer(serializers.ModelSerializer):
    fields_count = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = FormTemplate
        fields = (
            "id",
            "name",
            "description",
            "category",
            "category_display",
            "icon",
            "fields_schema",
            "fields_count",
            "is_system_template",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_fields_count(self, obj):
        return len(obj.fields_schema or [])
