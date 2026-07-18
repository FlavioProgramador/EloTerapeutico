"""Alias temporário para o módulo canônico de serializers de documentos gerados."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.serializers.generated_documents")
