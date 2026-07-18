"""Alias temporário para o módulo canônico do dashboard administrativo."""

from importlib import import_module
import sys

sys.modules[__name__] = import_module("apps.core.admin.dashboard")
