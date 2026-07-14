"""Casos de uso de formulários terapêuticos."""

from __future__ import annotations

from django.db import transaction

from apps.forms.models import FormField, TherapeuticForm


def replace_form_fields(*, form: TherapeuticForm, fields: list[dict]) -> None:
    form.fields.all().delete()
    FormField.objects.bulk_create(
        [
            FormField(
                form=form,
                type=field["type"],
                label=field["label"],
                placeholder=field.get("placeholder", ""),
                help_text=field.get("help_text", ""),
                required=field.get("required", False),
                order=field.get("order") or index,
                is_visible=field.get("is_visible", True),
                internal_id=field.get("internal_id", ""),
                config=field.get("config") or {},
            )
            for index, field in enumerate(fields, start=1)
        ]
    )


@transaction.atomic
def create_form(*, actor, validated_data: dict) -> TherapeuticForm:
    fields = validated_data.pop("fields", [])
    form = TherapeuticForm.objects.create(
        owner=actor,
        created_by=actor,
        updated_by=actor,
        **validated_data,
    )
    replace_form_fields(form=form, fields=fields)
    return form


@transaction.atomic
def update_form(*, actor, form: TherapeuticForm, validated_data: dict) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    fields = validated_data.pop("fields", None)
    for attr, value in validated_data.items():
        setattr(form, attr, value)
    form.updated_by = actor
    form.save()
    if fields is not None:
        replace_form_fields(form=form, fields=fields)
    return form


@transaction.atomic
def duplicate_form(*, actor, source: TherapeuticForm) -> TherapeuticForm:
    copy = TherapeuticForm.objects.create(
        owner=actor,
        name=f"{source.name} (cópia)",
        description=source.description,
        category=source.category,
        source_template=source.source_template,
        created_by=actor,
        updated_by=actor,
    )
    replace_form_fields(
        form=copy,
        fields=[
            {
                "type": field.type,
                "label": field.label,
                "placeholder": field.placeholder,
                "help_text": field.help_text,
                "required": field.required,
                "order": field.order,
                "is_visible": field.is_visible,
                "internal_id": field.internal_id,
                "config": field.config,
            }
            for field in source.fields.all()
        ],
    )
    return copy


@transaction.atomic
def archive_form(*, actor, form: TherapeuticForm) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    form.archive(actor)
    return form


@transaction.atomic
def restore_form(*, actor, form: TherapeuticForm) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    form.restore(actor)
    return form


@transaction.atomic
def delete_or_archive_form(*, actor, form: TherapeuticForm) -> tuple[TherapeuticForm | None, bool]:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    if form.submissions.exists():
        form.archive(actor)
        return form, False
    form.delete()
    return None, True
