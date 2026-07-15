"""Compatibilidade temporária para o prefixo legado ``/api/billing/``.

A rota canônica do módulo é ``/api/v1/billing/``. Este módulo clona os
callbacks atuais para evitar divergência funcional, mas adiciona headers de
depreciação e nomes de URL próprios para que ``reverse()`` nunca gere o
prefixo antigo por engano.
"""

from __future__ import annotations

from django.conf import settings
from django.urls.resolvers import URLPattern

from apps.billing.urls import urlpatterns as canonical_urlpatterns

DEFAULT_SUNSET = "Sun, 31 Jan 2027 23:59:59 GMT"
SUCCESSOR_PATH = "/api/v1/billing/"


def _add_deprecation_headers(response):
    response["Deprecation"] = "true"
    response["Sunset"] = getattr(
        settings,
        "BILLING_LEGACY_ROUTE_SUNSET",
        DEFAULT_SUNSET,
    )
    response["Link"] = f'<{SUCCESSOR_PATH}>; rel="successor-version"'
    response["Warning"] = '299 - "Deprecated API: use /api/v1/billing/"'
    return response


def _deprecated_callback(callback):
    def wrapped(request, *args, **kwargs):
        response = callback(request, *args, **kwargs)
        return _add_deprecation_headers(response)

    # Preserva o comportamento HTTP necessário sem copiar ``cls``/``actions``.
    # Assim o drf-spectacular não publica uma segunda árvore de endpoints.
    wrapped.__name__ = f"legacy_{getattr(callback, '__name__', 'billing_view')}"
    wrapped.__module__ = callback.__module__
    setattr(wrapped, "csrf_exempt", getattr(callback, "csrf_exempt", False))
    setattr(wrapped, "login_required", getattr(callback, "login_required", False))
    return wrapped


def _clone_pattern(pattern: URLPattern) -> URLPattern:
    legacy_name = f"legacy-{pattern.name}" if pattern.name else None
    return URLPattern(
        pattern.pattern,
        _deprecated_callback(pattern.callback),
        pattern.default_args,
        legacy_name,
    )


urlpatterns = [_clone_pattern(pattern) for pattern in canonical_urlpatterns]
