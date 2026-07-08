"""Composição das actions públicas do painel de pacientes."""

from apps.patients.actions.dashboard import PatientDashboardActions as LegacyDashboardActions
from apps.patients.actions.imports import PatientImportActions
from apps.patients.actions.metrics import PatientMetricsActions


class PatientDashboardActions(
    PatientImportActions,
    PatientMetricsActions,
    LegacyDashboardActions,
):
    pass


__all__ = ["PatientDashboardActions"]
