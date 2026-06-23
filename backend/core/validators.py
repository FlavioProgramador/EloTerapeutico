"""
core/validators.py
Validadores customizados reutilizáveis em todo o projeto.
"""

import re

from django.core.exceptions import ValidationError


def validate_cpf(value: str) -> None:
    """
    Valida CPF brasileiro — dígitos, pontos e traços são aceitos.
    Implementa o algoritmo oficial de verificação dos dois dígitos verificadores.
    """
    # Remove formatação
    cpf = re.sub(r"\D", "", value)

    if len(cpf) != 11:
        raise ValidationError("CPF deve conter 11 dígitos.")

    # CPFs com todos os dígitos iguais são inválidos (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")

    # Validação do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[9]):
        raise ValidationError("CPF inválido.")

    # Validação do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10 or resto == 11:
        resto = 0
    if resto != int(cpf[10]):
        raise ValidationError("CPF inválido.")


def validate_crp(value: str) -> None:
    """
    Valida número de CRP (Conselho Regional de Psicologia).
    Formato esperado: XX/XXXXXX (região/número)
    Ex: 06/123456
    """
    pattern = r"^\d{2}/\d{4,8}$"
    if not re.match(pattern, value):
        raise ValidationError(
            "CRP inválido. Use o formato XX/XXXXXX (ex: 06/123456)."
        )


def validate_phone(value: str) -> None:
    """
    Valida número de telefone brasileiro.
    Aceita formatos: (11) 99999-9999, 11999999999, +5511999999999
    """
    phone = re.sub(r"\D", "", value)
    if len(phone) not in (10, 11, 13):
        raise ValidationError(
            "Número de telefone inválido. Use o formato (11) 99999-9999."
        )
