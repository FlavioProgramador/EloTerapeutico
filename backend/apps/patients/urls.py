"""
apps/patients/urls.py
Configuração de rotas para o app de Pacientes.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

router = DefaultRouter()
router.register(r"", PatientViewSet, basename="patient")

urlpatterns = [
    path("", include(router.urls)),
]
