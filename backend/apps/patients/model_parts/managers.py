"""Gerenciadores do domínio de pacientes."""

from django.db import models


class PatientManager(models.Manager):
    """Exclui registros arquivados por soft delete."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllPatientsManager(models.Manager):
    """Inclui registros arquivados para auditoria e restauração."""

    def get_queryset(self):
        return super().get_queryset()
