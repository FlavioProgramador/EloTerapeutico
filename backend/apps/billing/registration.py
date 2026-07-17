"""Compatibilidade para o fluxo público de cadastro por plano."""

from .api.public.registration import PlanRegistrationView
from .api.public.serializers import PlanRegistrationSerializer

__all__ = ["PlanRegistrationSerializer", "PlanRegistrationView"]
