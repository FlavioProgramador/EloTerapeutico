"""Alias temporário para o módulo canônico de serializers de templates."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.serializers.document_templates")
