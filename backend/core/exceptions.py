"""
core/exceptions.py
Handler global de exceções para a API REST.
Retorna erros sempre no mesmo formato JSON, facilitando o tratamento no frontend.
"""

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler customizado que garante um envelope de resposta consistente:

    {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Descrição legível do erro.",
            "details": { ... }   # opcional, para erros de validação
        }
    }
    """
    # Primeiro deixa o DRF processar a exceção normalmente
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": {
                "code": _get_error_code(exc, response.status_code),
                "message": _get_error_message(exc, response),
                "details": response.data if isinstance(response.data, dict) else None,
            }
        }
        response.data = error_payload
        return response

    # Erros não tratados pelo DRF
    if isinstance(exc, ValidationError):
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": str(exc), "details": None}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {"error": {"code": "PERMISSION_DENIED", "message": "Você não tem permissão para realizar esta ação.", "details": None}},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, Http404):
        return Response(
            {"error": {"code": "NOT_FOUND", "message": "O recurso solicitado não foi encontrado.", "details": None}},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Erro interno inesperado
    logger.exception("Erro interno não tratado: %s", exc)
    return Response(
        {"error": {"code": "INTERNAL_ERROR", "message": "Ocorreu um erro interno. Por favor, tente novamente.", "details": None}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_code(exc, status_code: int) -> str:
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
    }
    # Tenta pegar o código específico do DRF
    if hasattr(exc, "default_code"):
        return exc.default_code.upper()
    return code_map.get(status_code, "ERROR")


def _get_error_message(exc, response) -> str:
    if hasattr(exc, "detail"):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list) and detail:
            return str(detail[0])
        if isinstance(detail, dict):
            # Pega a primeira mensagem de erro do dict
            for key, val in detail.items():
                if isinstance(val, list):
                    return f"{key}: {val[0]}"
                return f"{key}: {val}"
    return "Ocorreu um erro. Por favor, tente novamente."
