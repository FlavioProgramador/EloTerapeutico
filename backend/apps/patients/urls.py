"""Compatibilidade: rotas movidas para `apps.patients.api.urls`."""

from .api.urls import urlpatterns

__all__ = ["urlpatterns"]
