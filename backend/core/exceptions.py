"""Compatibilidade para imports antigos; use `apps.core.exceptions`."""

from apps.core.exceptions import custom_exception_handler

__all__ = ["custom_exception_handler"]
