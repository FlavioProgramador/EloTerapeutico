"""Exceções de aplicação e domínio seguras para exposição pela API."""

from __future__ import annotations

from typing import Any


class ApplicationError(Exception):
    """Base para exceções controladas que podem ser expostas pela API."""

    status_code = 400
    default_detail = "Ocorreu um erro na aplicação."
    default_code = "application_error"

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        *,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.detail = str(detail or self.default_detail)
        self.code = str(code or self.default_code)
        self.field = field
        if details is not None:
            self.details = details
        elif field:
            self.details = {field: [self.detail]}
        else:
            self.details = None
        super().__init__(self.detail)


class AuthorizationError(ApplicationError):
    """A identidade é válida, mas não possui acesso ao recurso (403)."""

    status_code = 403
    default_detail = "Você não tem permissão para realizar esta ação."
    default_code = "forbidden"


class ObjectNotFoundError(ApplicationError):
    """O recurso solicitado não existe ou não está visível ao ator (404)."""

    status_code = 404
    default_detail = "O recurso solicitado não foi encontrado."
    default_code = "not_found"


class DomainIntegrityError(ApplicationError):
    """O estado atual do domínio conflita com a operação solicitada (409)."""

    status_code = 409
    default_detail = "Erro de integridade ou conflito de dados."
    default_code = "domain_integrity_error"


class BusinessRuleViolation(ApplicationError):
    """Os dados são válidos, mas uma regra de negócio impede a operação (422)."""

    status_code = 422
    default_detail = "Violação de regra de negócio."
    default_code = "business_rule_violation"


class ApplicationOperationError(ApplicationError):
    """Uma operação controlada falhou sem expor detalhes internos (500)."""

    status_code = 500
    default_detail = "Não foi possível concluir a operação."
    default_code = "operation_failed"
