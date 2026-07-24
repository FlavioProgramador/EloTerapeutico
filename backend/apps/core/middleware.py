"""Middlewares transversais de observabilidade e headers defensivos."""

from __future__ import annotations

import re
from collections.abc import Callable
from contextvars import ContextVar
from uuid import uuid4

from django.conf import settings
from django.http import HttpRequest, HttpResponse

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_REQUEST_ID_CONTEXT: ContextVar[str] = ContextVar("elo_request_id", default="")


def get_current_request_id() -> str:
    """Retorna o identificador da requisição no contexto atual, quando existir."""

    return _REQUEST_ID_CONTEXT.get()


def resolve_request_id(request: HttpRequest) -> str:
    supplied = str(request.headers.get("X-Request-ID", "")).strip()
    if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return uuid4().hex


class RequestContextMiddleware:
    """Normaliza um correlation ID seguro e o devolve em todas as respostas."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = resolve_request_id(request)
        request.request_id = request_id
        token = _REQUEST_ID_CONTEXT.set(request_id)
        try:
            response = self.get_response(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            _REQUEST_ID_CONTEXT.reset(token)


class SecurityHeadersMiddleware:
    """Aplica headers adicionais sem sobrescrever decisões explícitas da view."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        self._set_if_missing(
            response,
            "Permissions-Policy",
            str(getattr(settings, "SECURITY_PERMISSIONS_POLICY", "")).strip(),
        )
        self._set_if_missing(
            response,
            "Cross-Origin-Resource-Policy",
            str(getattr(settings, "SECURITY_CROSS_ORIGIN_RESOURCE_POLICY", "")).strip(),
        )
        self._set_if_missing(response, "X-Permitted-Cross-Domain-Policies", "none")
        self._set_if_missing(
            response,
            "Content-Security-Policy",
            str(getattr(settings, "SECURITY_CONTENT_SECURITY_POLICY", "")).strip(),
        )
        return response

    @staticmethod
    def _set_if_missing(response: HttpResponse, name: str, value: str) -> None:
        if value and name not in response.headers:
            response.headers[name] = value


__all__ = [
    "RequestContextMiddleware",
    "SecurityHeadersMiddleware",
    "get_current_request_id",
    "resolve_request_id",
]
