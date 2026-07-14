"""Exceções de domínio do módulo de documentos."""


class DocumentDomainError(Exception):
    """Erro de domínio seguro para exposição pela API."""


__all__ = ["DocumentDomainError"]
