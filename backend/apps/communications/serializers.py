"""Compatibilidade para imports antigos de serializers.

Novos imports devem utilizar ``apps.communications.api.v1.serializers``.
"""

from .api.v1.serializers.automations import (
    CommunicationAutomationRunSerializer,
    CommunicationAutomationSerializer,
)
from .api.v1.serializers.communications import (
    CommunicationAttemptSerializer,
    CommunicationCreateSerializer,
    CommunicationDetailSerializer,
    CommunicationDraftUpdateSerializer,
    CommunicationListSerializer,
    CommunicationRecipientSerializer,
)
from .api.v1.serializers.legacy_channels import (
    CommunicationChannelConfigSerializer,
)
from .api.v1.serializers.notifications import (
    InAppNotificationSerializer,
    NotificationPreferenceSerializer,
)
from .api.v1.serializers.preferences import CommunicationPreferenceSerializer
from .api.v1.serializers.templates import CommunicationTemplateSerializer

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
