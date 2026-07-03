"""Compatibilidade para imports antigos; use `apps.core.validators`."""

from apps.core.validators import validate_cpf, validate_crp, validate_phone

__all__ = ["validate_cpf", "validate_crp", "validate_phone"]
