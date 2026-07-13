from __future__ import annotations

import re
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

PHONE_DIGITS_RE = re.compile(r"\D+")
SAFE_VARIABLE_KEYS = {
    "patient_name", "guardian_name", "therapist_name", "clinic_name",
    "appointment_date", "appointment_time", "appointment_duration",
    "appointment_location", "appointment_modality", "meeting_link",
    "confirmation_link", "cancellation_link", "reschedule_link",
    "form_name", "form_link", "form_due_date", "document_name",
    "document_link", "document_expiration_date", "payment_amount",
    "payment_due_date", "payment_status", "receipt_link",
    "package_remaining_sessions", "support_email",
}


class CommunicationBlocked(ValidationError):
    pass


class CommunicationLimitExceeded(PermissionDenied):
    default_detail = "Você atingiu o limite de comunicações do seu plano atual."


def mask_email(value: str) -> str:
    if "@" not in value:
        return "***"
    local, domain = value.split("@", 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{domain}"


def normalize_phone(value: str) -> str:
    digits = PHONE_DIGITS_RE.sub("", value or "")
    if not digits:
        return ""
    if len(digits) in {10, 11}:
        digits = f"55{digits}"
    if len(digits) < 12 or len(digits) > 15:
        raise ValidationError("Telefone inválido.")
    return digits


def mask_phone(value: str) -> str:
    digits = PHONE_DIGITS_RE.sub("", value or "")
    if len(digits) < 4:
        return "***"
    return f"+{digits[:2]} (***) *****-{digits[-4:]}"


def _safe_variables(variables: dict[str, object] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in (variables or {}).items():
        if key not in SAFE_VARIABLE_KEYS:
            continue
        if isinstance(value, Decimal):
            value = f"{value:.2f}"
        result[key] = str(value)[:500]
    return result
