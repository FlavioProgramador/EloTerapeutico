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
from .services import enforce_communication_access

__all__ = [
    "CanAccessCommunications",
    "CanManageCommunicationAutomations",
    "CanManageCommunicationChannels",
    "CanManageCommunicationTemplates",
    "CanRetryCommunication",
    "CanSendCommunication",
    "CanViewCommunicationLogs",
    "enforce_communication_access",
]
