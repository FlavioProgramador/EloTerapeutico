"""Serviços de health check compartilhados."""

from .services import collect_readiness_checks

__all__ = ["collect_readiness_checks"]
