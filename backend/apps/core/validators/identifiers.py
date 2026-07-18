"""Validadores reutilizáveis pelos domínios da aplicação."""

import re

from django.core.exceptions import ValidationError


def validate_cpf(value: str) -> None:
    cpf = re.sub(r"\D", "", value)
    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")

    first_digit = (sum(int(cpf[i]) * (10 - i) for i in range(9)) * 10) % 11
    if first_digit in (10, 11):
        first_digit = 0
    if first_digit != int(cpf[9]):
        raise ValidationError("CPF inválido.")

    second_digit = (sum(int(cpf[i]) * (11 - i) for i in range(10)) * 10) % 11
    if second_digit in (10, 11):
        second_digit = 0
    if second_digit != int(cpf[10]):
        raise ValidationError("CPF inválido.")


def validate_crp(value: str) -> None:
    if not re.match(r"^\d{2}/\d{4,8}$", value):
        raise ValidationError("CRP inválido. Use o formato XX/XXXXXX (ex: 06/123456).")


def validate_phone(value: str) -> None:
    phone = re.sub(r"\D", "", value)
    if len(phone) not in (10, 11, 13):
        raise ValidationError("Número de telefone inválido. Use o formato (11) 99999-9999.")
