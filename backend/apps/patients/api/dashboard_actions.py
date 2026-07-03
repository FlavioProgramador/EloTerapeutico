"""Composição das actions públicas do painel de pacientes."""

from ..actions.dashboard import PatientDashboardActions as LegacyDashboardActions
from ..actions.imports import PatientImportActions
from ..actions.metrics import PatientMetricsActions


class PatientDashboardActions(
    PatientImportActions,
    PatientMetricsActions,
    LegacyDashboardActions,
):
    pass


__all__ = ["PatientDashboardActions"]
