"""Compatibilidade para o client Asaas.

A implementação canônica está em ``apps.billing.integrations.asaas.client``.
O objeto ``httpx`` permanece exposto somente para preservar patch points de
testes e integrações legadas durante a transição.
"""

from apps.billing.integrations.asaas.client import AsaasGateway, httpx

__all__ = ["AsaasGateway", "httpx"]
