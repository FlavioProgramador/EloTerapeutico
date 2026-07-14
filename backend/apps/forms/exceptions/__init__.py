"""Exceções de domínio de Formulários."""


class FormsDomainError(Exception):
    """Erro controlado do domínio de formulários."""


class InvalidFormAnswerError(FormsDomainError):
    """Resposta referencia um campo que não pertence ao formulário."""


class FinalizedSubmissionError(FormsDomainError):
    """Submissão finalizada não pode ser alterada ou reenviada."""


__all__ = ["FinalizedSubmissionError", "FormsDomainError", "InvalidFormAnswerError"]
