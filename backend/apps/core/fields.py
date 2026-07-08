"""Campos Django compartilhados para dados sensíveis."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _derive_key(raw_key: str) -> bytes:
    hashed = hashlib.sha256(raw_key.encode()).digest()
    return base64.urlsafe_b64encode(hashed)


def encrypt_value(value: str) -> str:
    if not value:
        return value

    if hasattr(settings, "FIELD_ENCRYPTION_KEY_V2"):
        key = settings.FIELD_ENCRYPTION_KEY_V2
        version = "v2"
    else:
        key = settings.FIELD_ENCRYPTION_KEY
        version = "v1"

    fernet = Fernet(_derive_key(key))
    ciphertext = fernet.encrypt(value.encode()).decode()
    return f"{version}:{ciphertext}"


def decrypt_value(token: str) -> str:
    if not token:
        return token

    try:
        version, ciphertext = token.split(":", 1)
    except ValueError:
        ciphertext, version = token, "v1"

    key = getattr(
        settings, f"FIELD_ENCRYPTION_KEY_{version.upper()}", settings.FIELD_ENCRYPTION_KEY
    )
    fernet = Fernet(_derive_key(key))
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError, TypeError):
        return "[DADO INACESSÍVEL]"


class EncryptedTextField(models.TextField):
    """TextField que criptografa valores antes da persistência."""

    def from_db_value(self, value, expression, connection):
        if value is None or not isinstance(value, str):
            return value
        return decrypt_value(value)

    def to_python(self, value):
        return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return encrypt_value(value)
