"""Registro dos signals do app de comunicações.

A importação dos módulos abaixo é intencional: os decorators ``receiver``
registram cada handler uma única vez quando o ``AppConfig.ready`` é executado.
"""

from . import agenda, documents, finance, forms, users

__all__ = ["agenda", "documents", "finance", "forms", "users"]
