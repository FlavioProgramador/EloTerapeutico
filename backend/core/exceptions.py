"""Handler global e padronizado de exceções da API REST."""

from __future__ import annotations

import logging
import re
import secrets

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import OperationalError, ProgrammingError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _get_request_id(context) -> str:
    request = context.get("request") if isinstance(context, dict) else None
    supplied = ""
    if request is not None:
        supplied = str(request.headers.get("X-Request-ID", ""))
    if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return secrets.token_hex(16)


def _secure_error_response(response: Response, request_id: str) -> Response:
    response["X-Request-ID"] = request_id
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def custom_exception_handler(exc, context):
    request_id = _get_request_id(context)
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error": {
                "code": _get_error_code(exc, response.status_code),
                "message": _get_error_message(exc, response),
                "details": response.data if isinstance(response.data, dict) else None,
            }
        }
        return _secure_error_response(response, request_id)

    if isinstance(exc, ValidationError):
        response = Response(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": _validation_error_message(exc),
                    "details": None,
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
        return _secure_error_response(response, request_id)

    if isinstance(exc, PermissionDenied):
        response = Response(
            {
                "error": {
                    "code": "PERMISSION_DENIED",
                    "message": "Você não tem permissão para realizar esta ação.",
                    "details": None,
                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )
        return _secure_error_response(response, request_id)

    if isinstance(exc, Http404):
        response = Response(
            {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "O recurso solicitado não foi encontrado.",
                    "details": None,
                }
            },
            status=status.HTTP_404_NOT_FOUND,
        )
        return _secure_error_response(response, request_id)

    if isinstance(exc, (OperationalError, ProgrammingError)) and _is_communications_view(context):
        logger.error(
            "communications_database_not_ready",
            extra={
                "request_id": request_id,
                "exception_type": exc.__class__.__name__,
                "view": _view_name(context),
            },
        )
        response = Response(
            {
                "error": {
                    "code": "COMMUNICATIONS_DATABASE_NOT_READY",
                    "message": (
                        "O banco do módulo de Comunicações ainda não está disponível. "
                        "Aplique as migrations do backend e reinicie os serviços."
                    ),
                    "details": None,
                }
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        return _secure_error_response(response, request_id)

    # Não use logger.exception aqui: a representação textual da exceção pode
    # conter SQL, tokens, CPF ou conteúdo clínico. O tipo e o request_id são
    # suficientes para correlação; detalhes devem ser coletados por uma solução
    # de observabilidade com redaction explícita.
    logger.error(
        "api_unhandled_exception",
        extra={
            "request_id": request_id,
            "exception_type": exc.__class__.__name__,
            "view": _view_name(context),
        },
    )
    response = Response(
        {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Ocorreu um erro interno. Por favor, tente novamente.",
                "details": None,
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    return _secure_error_response(response, request_id)


def _validation_error_message(exc: ValidationError) -> str:
    messages = getattr(exc, "messages", None)
    if messages:
        return str(messages[0])
    return "Os dados enviados são inválidos."


def _view_name(context) -> str:
    view = context.get("view") if isinstance(context, dict) else None
    return view.__class__.__name__ if view is not None else "unknown"


def _is_communications_view(context) -> bool:
    view = context.get("view") if isinstance(context, dict) else None
    module = view.__class__.__module__ if view is not None else ""
    return module.startswith("apps.communications.")


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
        503: "SERVICE_UNAVAILABLE",
    }
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
            for key, value in detail.items():
                if isinstance(value, list):
                    return f"{key}: {value[0]}"
                return f"{key}: {value}"
    return "Ocorreu um erro. Por favor, tente novamente."
