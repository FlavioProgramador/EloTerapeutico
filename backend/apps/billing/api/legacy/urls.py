"""Compatibilidade temporária para o prefixo legado ``/api/billing/``."""

from __future__ import annotations

from typing import Any, cast

from django.conf import settings
from django.urls.resolvers import URLPattern

from apps.billing.api.v1.urls import urlpatterns as canonical_urlpatterns

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

    wrapped.__name__ = f"legacy_{getattr(callback, '__name__', 'billing_view')}"
    wrapped.__module__ = callback.__module__
    wrapped_with_attrs = cast(Any, wrapped)
    wrapped_with_attrs.csrf_exempt = getattr(callback, "csrf_exempt", False)
    wrapped_with_attrs.login_required = getattr(callback, "login_required", False)
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

__all__ = ["DEFAULT_SUNSET", "SUCCESSOR_PATH", "urlpatterns"]
