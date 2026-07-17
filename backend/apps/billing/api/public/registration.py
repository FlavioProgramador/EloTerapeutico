"""Compatibilidade para o endpoint público de cadastro.

A implementação canônica está em ``apps.billing.api.public.views.registration``.
"""

from .views.registration import PlanRegistrationView

__all__ = ["PlanRegistrationView"]
