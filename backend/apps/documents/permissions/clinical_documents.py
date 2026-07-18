"""Alias temporário para a permission canônica de documentos clínicos."""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("apps.documents.api.v1.permissions.clinical_documents")
