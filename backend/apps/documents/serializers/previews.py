"""Alias temporário para o módulo canônico de serializers de prévia."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.serializers.previews")
