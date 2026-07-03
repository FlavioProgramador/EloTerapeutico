"""Compatibilidade para migrations antigas; use `apps.core.fields`."""

from apps.core.fields import (
    EncryptedTextField,
    decrypt_value,
    encrypt_value,
)

__all__ = ["EncryptedTextField", "decrypt_value", "encrypt_value"]
