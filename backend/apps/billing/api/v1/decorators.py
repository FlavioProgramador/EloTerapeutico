"""Compatibilidade temporária para decorators de acesso da API v1."""

from apps.billing.api.access import require_feature

__all__ = ["require_feature"]
