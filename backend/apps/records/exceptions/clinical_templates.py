"""Exceções de domínio para templates clínicos."""


class ClinicalTemplateDomainError(Exception):
    """Erro controlado do domínio de templates clínicos."""


class InvalidClinicalTemplateAction(ClinicalTemplateDomainError):
    """Ação solicitada não é suportada pelo template clínico."""


__all__ = ["ClinicalTemplateDomainError", "InvalidClinicalTemplateAction"]
