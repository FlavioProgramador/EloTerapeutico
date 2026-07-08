"""Importação transacional e testável de pacientes por CSV."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from io import StringIO

from django.db import transaction

from apps.patients.api.serializers.form_serializers import PatientFormSerializer

from ..models import Patient


class PatientImportError(ValueError):
    """Erro previsível de contrato do arquivo de importação."""


@dataclass
class PatientImportResult:
    total: int
    valid: int
    duplicates: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    imported: int = 0

    @property
    def ready(self) -> bool:
        return not self.duplicates and not self.errors

    def as_dict(self) -> dict:
        data = {
            "total": self.total,
            "valid": self.valid,
            "duplicates": self.duplicates,
            "errors": self.errors,
            "ready": self.ready,
        }
        if self.imported:
            data["imported"] = self.imported
        return data


def _cell(row: dict, key: str, default: str = "") -> str:
    value = row.get(key, default)
    return default if value is None else str(value).strip()


def _read_rows(uploaded_file) -> list[dict]:
    if uploaded_file.size > 2 * 1024 * 1024:
        raise PatientImportError("O arquivo deve possuir até 2 MB.")
    try:
        content = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PatientImportError("Utilize um CSV codificado em UTF-8.") from exc

    reader = csv.DictReader(StringIO(content))
    required = {"full_name", "cpf", "birth_date"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise PatientImportError("O CSV deve conter as colunas full_name, cpf e birth_date.")
    rows = list(reader)
    if not rows:
        raise PatientImportError("O arquivo CSV não possui registros.")
    if len(rows) > 500:
        raise PatientImportError("Importe no máximo 500 pacientes por vez.")
    return rows


def preview_patient_import(*, uploaded_file, therapist):
    rows = _read_rows(uploaded_file)
    normalized_cpfs = {re.sub(r"\D", "", _cell(row, "cpf")) for row in rows if _cell(row, "cpf")}
    existing_cpfs = set(
        Patient.all_objects.filter(cpf__in=normalized_cpfs).values_list(
            "cpf",
            flat=True,
        )
    )

    valid_payloads = []
    errors = []
    duplicates = []
    seen_cpfs: set[str] = set()

    for line, row in enumerate(rows, start=2):
        raw_cpf = _cell(row, "cpf")
        clean_cpf = re.sub(r"\D", "", raw_cpf)
        if clean_cpf and (clean_cpf in seen_cpfs or clean_cpf in existing_cpfs):
            duplicates.append({"line": line, "cpf": raw_cpf})
            continue
        if clean_cpf:
            seen_cpfs.add(clean_cpf)

        payload = {
            "full_name": _cell(row, "full_name"),
            "cpf": raw_cpf,
            "birth_date": _cell(row, "birth_date"),
            "email": _cell(row, "email"),
            "phone": _cell(row, "phone"),
            "gender": _cell(row, "gender", "N") or "N",
            "status": _cell(row, "status", "active") or "active",
            "modality": _cell(row, "modality", "in_person") or "in_person",
            "payer_type": _cell(row, "payer_type", "private") or "private",
            "therapist": therapist.pk,
        }
        serializer = PatientFormSerializer(
            data=payload,
            context={"actor": therapist},
        )
        if serializer.is_valid():
            valid_payloads.append(serializer.validated_data)
        else:
            errors.append({"line": line, "errors": serializer.errors})

    result = PatientImportResult(
        total=len(rows),
        valid=len(valid_payloads),
        duplicates=duplicates,
        errors=errors,
    )
    return result, valid_payloads


@transaction.atomic
def import_patients_from_csv(*, uploaded_file, therapist, confirm: bool):
    result, payloads = preview_patient_import(
        uploaded_file=uploaded_file,
        therapist=therapist,
    )
    if not confirm or not result.ready:
        return result

    for payload in payloads:
        Patient.objects.create(**payload)
    result.imported = len(payloads)
    return result
