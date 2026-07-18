"""Rotas HTTP transversais do app core."""

from django.urls import path

from apps.core.api.views.health import liveness, readiness

urlpatterns = [
    path("live/", liveness, name="health-live"),
    path("ready/", readiness, name="health-ready"),
]
