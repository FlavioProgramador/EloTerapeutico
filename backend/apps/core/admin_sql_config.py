"""Configuração segura do SQL Explorer administrativo.

Este módulo não importa Django para poder ser utilizado durante a carga dos
settings, antes da inicialização do app registry.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

SQL_EXPLORER_LINK = "/admin/sql-explorer/"


def configure_unfold_navigation(unfold_config: MutableMapping[str, Any], *, enabled: bool) -> None:
    """Adiciona ou remove o atalho do SQL Explorer no menu do Unfold.

    A rota não deve ser sugerida quando a feature flag estiver desligada. O
    helper é idempotente para evitar duplicação durante imports/reloads dos
    settings em testes.
    """

    navigation = unfold_config.get("SIDEBAR", {}).get("navigation", [])
    if not navigation:
        return

    general_items = navigation[0].setdefault("items", [])
    general_items[:] = [item for item in general_items if item.get("link") != SQL_EXPLORER_LINK]

    if enabled:
        general_items.append(
            {
                "title": "SQL Explorer",
                "icon": "database",
                "link": SQL_EXPLORER_LINK,
            }
        )
