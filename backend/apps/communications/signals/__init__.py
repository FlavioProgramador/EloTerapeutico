"""Registro dos signals do app de comunicações.

A importação dos módulos abaixo é intencional: os decorators ``receiver``
registram cada handler uma única vez quando o ``AppConfig.ready`` é executado.
"""

from . import documents, finance, forms, scheduling, users

__all__ = ["documents", "finance", "forms", "scheduling", "users"]
