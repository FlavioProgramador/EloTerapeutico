"""Compatibilidade para criação de recursos derivados."""

from apps.scheduling.services.resources import create_appointment_resources, mask_phone

__all__ = ["create_appointment_resources", "mask_phone"]
