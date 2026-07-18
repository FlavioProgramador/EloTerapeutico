"""Alias temporário para a view canônica de placeholders."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.views.placeholders")
