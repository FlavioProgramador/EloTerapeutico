from rest_framework import serializers

from apps.forms.models import FieldType, FormField

OPTION_FIELDS = {FieldType.SELECT, FieldType.RADIO, FieldType.CHECKBOX}
ALLOWED_FIELD_TYPES = {choice.value for choice in FieldType}


def normalize_options(config: dict) -> list[str]:
    options = config.get("options", [])
    if not isinstance(options, list):
        raise serializers.ValidationError("As opções devem ser uma lista.")
    normalized = [str(item).strip() for item in options if str(item).strip()]
    if not normalized:
        raise serializers.ValidationError("Campos de seleção precisam ter ao menos uma opção.")
    return normalized


def validate_field_payload(field: dict) -> dict:
    field_type = field.get("type")
    if field_type not in ALLOWED_FIELD_TYPES:
        raise serializers.ValidationError({"type": "Tipo de campo inválido."})
    label = str(field.get("label", "")).strip()
    if not label:
        raise serializers.ValidationError({"label": "Informe o nome do campo."})
    config = field.get("config") or {}
    if not isinstance(config, dict):
        raise serializers.ValidationError({"config": "Configuração inválida."})
    if field_type in OPTION_FIELDS:
        config["options"] = normalize_options(config)
    if field_type == FieldType.SCALE:
        min_value = int(config.get("min", 1))
        max_value = int(config.get("max", 10))
        if min_value >= max_value:
            raise serializers.ValidationError({"config": "O valor mínimo da escala deve ser menor que o máximo."})
        config["min"] = min_value
        config["max"] = max_value
        config["step"] = int(config.get("step", 1))
    field["label"] = label[:180]
    field["placeholder"] = str(field.get("placeholder", ""))[:255]
    field["help_text"] = str(field.get("help_text", ""))[:255]
    field["config"] = config
    return field


class FormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField
        fields = (
            "id",
            "type",
            "label",
            "placeholder",
            "help_text",
            "required",
            "order",
            "is_visible",
            "internal_id",
            "config",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        return validate_field_payload(attrs)
