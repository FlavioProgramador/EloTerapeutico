from django.urls import path

from apps.core.health import liveness, readiness

urlpatterns = [
    path("live/", liveness, name="health-live"),
    path("ready/", readiness, name="health-ready"),
]
