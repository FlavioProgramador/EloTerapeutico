"""Fachada de compatibilidade para modelos de formulários.

Os modelos ficam organizados em `model_parts/`, preservando imports públicos
como `from apps.forms.models import TherapeuticForm`.
"""

from .model_parts import (
    FieldType,
    FormAnswer,
    FormCategory,
    FormField,
    FormSubmission,
    FormTemplate,
    TherapeuticForm,
)

__all__ = [
    "FieldType",
    "FormAnswer",
    "FormCategory",
    "FormField",
    "FormSubmission",
    "FormTemplate",
    "TherapeuticForm",
]
