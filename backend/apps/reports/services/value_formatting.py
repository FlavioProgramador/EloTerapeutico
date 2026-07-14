"""Formatação de valores exibidos nos relatórios."""

from decimal import Decimal

from apps.patients.models import Patient


def decimal_to_number(value: Decimal | int | float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def insurance_label(patient: Patient | None) -> str:
    if not patient:
        return "Sem convenio"
    if patient.payer_type == Patient.PayerType.INSURANCE:
        return patient.insurance_name or "Sem convenio"
    return "Particular"
