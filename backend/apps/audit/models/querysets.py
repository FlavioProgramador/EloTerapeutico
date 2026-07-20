"""QuerySet append-only dos registros de auditoria."""

from __future__ import annotations

from django.db import models

from apps.audit.exceptions import AuditLogImmutableError

_IMMUTABLE_MESSAGE = "Logs de auditoria são append-only e não podem ser alterados ou removidos."


class AuditLogQuerySet(models.QuerySet):
    """Permite leitura e inserção, bloqueando mutações em registros existentes."""

    def update(self, **kwargs):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    async def aupdate(self, **kwargs):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    def delete(self):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    async def adelete(self):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    def bulk_update(self, objs, fields, batch_size=None):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    async def abulk_update(self, objs, fields, batch_size=None):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)

    async def aupdate_or_create(self, defaults=None, create_defaults=None, **kwargs):
        raise AuditLogImmutableError(_IMMUTABLE_MESSAGE)


AuditLogManager = models.Manager.from_queryset(AuditLogQuerySet)

__all__ = ["AuditLogManager", "AuditLogQuerySet"]
