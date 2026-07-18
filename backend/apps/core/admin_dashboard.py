"""Alias temporário para o módulo canônico do dashboard administrativo."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.core.admin.dashboard")
