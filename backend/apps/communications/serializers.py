"""Compatibilidade para imports antigos de serializers.

Novos imports devem utilizar ``apps.communications.api.v1.serializers``.
"""

from .api.v1.serializers.communications import (
    CommunicationAttemptSerializer,
    CommunicationAutomationRunSerializer,
    CommunicationAutomationSerializer,
    CommunicationChannelConfigSerializer,
    CommunicationCreateSerializer,
    CommunicationDetailSerializer,
    CommunicationDraftUpdateSerializer,
    CommunicationListSerializer,
    CommunicationPreferenceSerializer,
    CommunicationRecipientSerializer,
    CommunicationTemplateSerializer,
    InAppNotificationSerializer,
    NotificationPreferenceSerializer,
)

__all__ = [
    "CommunicationAttemptSerializer",
    "CommunicationAutomationRunSerializer",
    "CommunicationAutomationSerializer",
    "CommunicationChannelConfigSerializer",
    "CommunicationCreateSerializer",
    "CommunicationDetailSerializer",
    "CommunicationDraftUpdateSerializer",
    "CommunicationListSerializer",
    "CommunicationPreferenceSerializer",
    "CommunicationRecipientSerializer",
    "CommunicationTemplateSerializer",
    "InAppNotificationSerializer",
    "NotificationPreferenceSerializer",
]
