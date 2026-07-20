"""Extração segura do contexto HTTP de auditoria."""

from __future__ import annotations

import ipaddress
import re

from django.conf import settings

from apps.audit.types import AuditRequestContext

from .sanitization import MAX_USER_AGENT_LENGTH, clean_text

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _valid_ip(value: object) -> str | None:
    candidate = str(value or "").strip()
    if not candidate:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _forwarded_ip(request) -> str | None:
    trusted_hops = max(int(getattr(settings, "AUDIT_TRUSTED_PROXY_HOPS", 0) or 0), 0)
    legacy_trust = bool(getattr(settings, "TRUST_PROXY_CLIENT_IP_HEADERS", False))
    if not trusted_hops and not legacy_trust:
        return None

    azure_client_ip = _valid_ip(request.META.get("HTTP_X_AZURE_CLIENTIP"))
    if azure_client_ip:
        return azure_client_ip

    forwarded = [
        part.strip()
        for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
    ]
    valid_forwarded = [ip for ip in (_valid_ip(part) for part in forwarded) if ip]
    if not valid_forwarded:
        return None
    if legacy_trust and not trusted_hops:
        return valid_forwarded[0]
    if trusted_hops > len(valid_forwarded):
        return None
    return valid_forwarded[-trusted_hops]


def _request_id(request) -> str | None:
    supplied = str(
        request.META.get("HTTP_X_REQUEST_ID")
        or getattr(request, "headers", {}).get("X-Request-ID", "")
    )
    if supplied and _REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return None


def extract_request_context(request=None) -> AuditRequestContext:
    if request is None:
        return AuditRequestContext(ip_address=None, user_agent="", request_id=None)
    ip_address = _forwarded_ip(request) or _valid_ip(request.META.get("REMOTE_ADDR"))
    user_agent = clean_text(
        request.META.get("HTTP_USER_AGENT", ""),
        max_length=MAX_USER_AGENT_LENGTH,
    )
    return AuditRequestContext(
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=_request_id(request),
    )


__all__ = ["extract_request_context"]
