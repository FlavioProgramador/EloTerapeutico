"""
core/fields.py
Campos customizados do Django para armazenamento seguro de dados sensíveis.
Usa criptografia simétrica AES-128-CBC via biblioteca `cryptography`.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _get_fernet() -> Fernet:
    """
    Deriva uma chave Fernet de 32 bytes a partir da FIELD_ENCRYPTION_KEY
    configurada nas settings. A chave é codificada em base64-url-safe.
    """
    raw_key = settings.FIELD_ENCRYPTION_KEY.encode()
    hashed = hashlib.sha256(raw_key).digest()
    fernet_key = base64.urlsafe_b64encode(hashed)
    return Fernet(fernet_key)


def encrypt_value(value: str) -> str:
    """Criptografa uma string e retorna o token base64 como string."""
    if not value:
        return value
    fernet = _get_fernet()
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(token: str) -> str:
    """Descriptografa um token Fernet e retorna a string original."""
    if not token:
        return token
    try:
        fernet = _get_fernet()
        return fernet.decrypt(token.encode()).decode()
    except (InvalidToken, Exception):
        return "[DADO INACESSÍVEL]"


class EncryptedTextField(models.TextField):
    """
    TextField que criptografa o valor antes de salvar no banco de dados
    e descriptografa ao carregar. Transparente para o código da aplicação.

    Uso:
        content = EncryptedTextField()
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        # Se já está em texto puro (não é um token Fernet), retorna diretamente
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_value(value)
