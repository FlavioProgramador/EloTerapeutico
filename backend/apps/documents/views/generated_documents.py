"""Alias temporário para o módulo canônico de views de documentos gerados."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.views.generated_documents")
