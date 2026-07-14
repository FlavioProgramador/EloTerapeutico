"""Casos de uso transacionais do prontuário eletrônico."""

from .clinical_templates import (
    apply_clinical_template_action,
    archive_clinical_template,
    create_clinical_template,
    duplicate_clinical_template,
    update_clinical_template,
)

__all__ = [
    "apply_clinical_template_action",
    "archive_clinical_template",
    "create_clinical_template",
    "duplicate_clinical_template",
    "update_clinical_template",
]
