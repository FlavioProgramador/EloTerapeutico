"""Compatibilidade para o serializer de configuração de canais.

Novos imports devem utilizar
``apps.communications.api.v1.serializers.channels``.
"""

from .api.v1.serializers.channels import CommunicationChannelConfigSerializer

__all__ = ["CommunicationChannelConfigSerializer"]
