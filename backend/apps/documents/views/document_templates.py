"""Alias temporário para o módulo canônico de views de templates."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.views.document_templates")
