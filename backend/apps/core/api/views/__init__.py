"""Views transversais da API."""

from .health import liveness, readiness

__all__ = ["liveness", "readiness"]
