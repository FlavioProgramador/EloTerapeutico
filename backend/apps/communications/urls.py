"""Fachada estável das rotas autenticadas de comunicações."""

from .api.v1.urls import router, urlpatterns

__all__ = ["router", "urlpatterns"]
