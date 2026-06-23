"""
apps/records/urls.py
Configuração de rotas para o app de Prontuários (Records).
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import AnamnesisView, EvolutionViewSet

router = DefaultRouter()
router.register(r"evolutions", EvolutionViewSet, basename="evolution")

urlpatterns = [
    # Rota da Anamnese inicial do Paciente
    path("patients/<int:patient_id>/anamnesis/", AnamnesisView.as_view(), name="patient-anamnesis"),
    # Rotas de Evoluções e Aditivos
    path("", include(router.urls)),
]
