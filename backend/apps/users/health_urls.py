from django.urls import path

from .api.views import HealthCheckView

urlpatterns = [path("", HealthCheckView.as_view(), name="health-check")]
