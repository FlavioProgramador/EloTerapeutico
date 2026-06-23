"""
apps/agenda/urls.py
Configuração de rotas para o app de Agenda.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
]
