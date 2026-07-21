"""Casos de uso de formulários terapêuticos."""

from __future__ import annotations

from django.db import transaction

from apps.forms.models import FormField, TherapeuticForm
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability
from rest_framework.exceptions import PermissionDenied


def _membership(*, actor, organization=None):
    memberships = OrganizationMembership.objects.filter(
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    if organization is not None:
        membership = memberships.filter(organization=organization).first()
    else:
        membership = memberships.filter(is_default=True).first()
        if membership is None:
            first_two = list(memberships[:2])
            membership = first_two[0] if len(first_two) == 1 else None
    if membership is None or not has_capability(membership, "forms.manage"):
        raise PermissionDenied("Você não pode gerenciar formulários nesta organização.")
    return membership


def _ensure_form_access(*, actor, form, organization=None):
    membership = _membership(
        actor=actor,
        organization=organization or form.organization,
    )
    if form.organization_id != membership.organization_id:
        raise PermissionDenied("O formulário pertence a outra organização.")
    if (
        membership.role == OrganizationMembership.Role.THERAPIST
        and form.owner_id != actor.pk
    ):
        raise PermissionDenied("O formulário pertence a outro profissional.")
    return membership


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
def create_form(*, actor, validated_data: dict, organization=None) -> TherapeuticForm:
    membership = _membership(actor=actor, organization=organization)
    fields = validated_data.pop("fields", [])
    form = TherapeuticForm(
        organization=membership.organization,
        owner=actor,
        created_by=actor,
        updated_by=actor,
        **validated_data,
    )
    form.full_clean()
    form.save()
    replace_form_fields(form=form, fields=fields)
    return form


@transaction.atomic
def update_form(
    *,
    actor,
    form: TherapeuticForm,
    validated_data: dict,
    organization=None,
) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().select_related(
        "organization",
        "owner",
        "source_template",
    ).get(pk=form.pk)
    _ensure_form_access(actor=actor, form=form, organization=organization)
    fields = validated_data.pop("fields", None)
    for attr, value in validated_data.items():
        setattr(form, attr, value)
    form.updated_by = actor
    form.full_clean()
    form.save()
    if fields is not None:
        replace_form_fields(form=form, fields=fields)
    return form


@transaction.atomic
def duplicate_form(
    *,
    actor,
    source: TherapeuticForm,
    organization=None,
) -> TherapeuticForm:
    membership = _ensure_form_access(
        actor=actor,
        form=source,
        organization=organization,
    )
    copy = TherapeuticForm.objects.create(
        organization=membership.organization,
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
def archive_form(*, actor, form: TherapeuticForm, organization=None) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    _ensure_form_access(actor=actor, form=form, organization=organization)
    form.archive(actor)
    return form


@transaction.atomic
def restore_form(*, actor, form: TherapeuticForm, organization=None) -> TherapeuticForm:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    _ensure_form_access(actor=actor, form=form, organization=organization)
    form.restore(actor)
    return form


@transaction.atomic
def delete_or_archive_form(
    *,
    actor,
    form: TherapeuticForm,
    organization=None,
) -> tuple[TherapeuticForm | None, bool]:
    form = TherapeuticForm.objects.select_for_update().get(pk=form.pk)
    _ensure_form_access(actor=actor, form=form, organization=organization)
    if form.submissions.exists():
        form.archive(actor)
        return form, False
    form.delete()
    return None, True
