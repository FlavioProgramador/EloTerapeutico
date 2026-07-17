"""Compatibilidade para imports antigos de permissões.

Novos imports devem utilizar ``apps.communications.api.v1.permissions``.
"""

from .api.v1.permissions import (
    CanAccessCommunications,
    CanManageCommunicationAutomations,
    CanManageCommunicationChannels,
    CanManageCommunicationTemplates,
    CanRetryCommunication,
    CanSendCommunication,
    CanViewCommunicationLogs,
)

__all__ = [
    "CanAccessCommunications",
    "CanManageCommunicationAutomations",
    "CanManageCommunicationChannels",
    "CanManageCommunicationTemplates",
    "CanRetryCommunication",
    "CanSendCommunication",
    "CanViewCommunicationLogs",
]
