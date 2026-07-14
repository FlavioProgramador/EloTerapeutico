"""Recursos transversais compartilhados pelos apps do Elo Terapêutico."""

from apps.core.exceptions import (
    ApplicationError,
    ApplicationOperationError,
    AuthorizationError,
    BusinessRuleViolation,
    DomainIntegrityError,
    ObjectNotFoundError,
)

__all__ = [
    "ApplicationError",
    "ApplicationOperationError",
    "AuthorizationError",
    "BusinessRuleViolation",
    "DomainIntegrityError",
    "ObjectNotFoundError",
]
