"""Alias temporário para o módulo canônico do SQL Explorer."""

from importlib import import_module
import sys

sys.modules[__name__] = import_module("apps.core.admin.sql")
