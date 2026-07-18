"""Alias temporário para o módulo canônico do SQL Explorer."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.core.admin.sql")
