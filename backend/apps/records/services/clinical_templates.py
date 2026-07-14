"""Casos de uso de templates de evolução clínica."""

from __future__ import annotations

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.records.exceptions import InvalidClinicalTemplateAction
from apps.records.models.templates import ClinicalEvolutionTemplate


@transaction.atomic
def create_clinical_template(
    *,
    actor,
    validated_data: dict,
    is_system: bool = False,
) -> ClinicalEvolutionTemplate:
    return ClinicalEvolutionTemplate.objects.create(
        owner=None if is_system else actor,
        **validated_data,
    )


@transaction.atomic
def update_clinical_template(
    *,
    template: ClinicalEvolutionTemplate,
    validated_data: dict,
) -> ClinicalEvolutionTemplate:
    template = ClinicalEvolutionTemplate.objects.select_for_update().get(pk=template.pk)
    for field, value in validated_data.items():
        setattr(template, field, value)
    template.save()
    return template


@transaction.atomic
def archive_clinical_template(*, template: ClinicalEvolutionTemplate) -> ClinicalEvolutionTemplate:
    template = ClinicalEvolutionTemplate.objects.select_for_update().get(pk=template.pk)
    template.is_active = False
    template.archived_at = timezone.now()
    template.save(update_fields=["is_active", "archived_at", "updated_at"])
    return template


@transaction.atomic
def duplicate_clinical_template(
    *,
    actor,
    template: ClinicalEvolutionTemplate,
) -> ClinicalEvolutionTemplate:
    base_name = f"Cópia de {template.name}"
    name = base_name
    suffix = 2
    while ClinicalEvolutionTemplate.objects.filter(owner=actor, name=name).exists():
        name = f"{base_name} ({suffix})"
        suffix += 1
    return ClinicalEvolutionTemplate.objects.create(
        owner=actor,
        name=name,
        description=template.description,
        category=template.category,
        specialty=template.specialty,
        content=template.content,
        is_active=True,
        sort_order=template.sort_order,
    )


@transaction.atomic
def apply_clinical_template_action(
    *,
    template: ClinicalEvolutionTemplate,
    action: str,
) -> ClinicalEvolutionTemplate:
    template = ClinicalEvolutionTemplate.objects.select_for_update().get(pk=template.pk)
    if action == "activate":
        template.is_active = True
        template.archived_at = None
    elif action == "deactivate":
        template.is_active = False
        template.archived_at = None
    elif action == "archive":
        template.is_active = False
        template.archived_at = timezone.now()
    elif action == "mark_used":
        ClinicalEvolutionTemplate.objects.filter(pk=template.pk).update(usage_count=F("usage_count") + 1)
        template.refresh_from_db()
        return template
    else:
        raise InvalidClinicalTemplateAction("Ação inválida.")
    template.save(update_fields=["is_active", "archived_at", "updated_at"])
    return template
