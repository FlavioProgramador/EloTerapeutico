"""Alias de módulo para os services canônicos de consultas."""

import sys
from importlib import import_module

_canonical = import_module("apps.scheduling.services.appointments")

if not hasattr(_canonical, "create_financial_transaction"):
    _canonical.create_financial_transaction = _canonical.create_appointment_transaction

    def _compat_create_appointment_transaction(*, appointment):
        return _canonical.create_financial_transaction(appointment=appointment)

    _canonical.create_appointment_transaction = _compat_create_appointment_transaction

if not hasattr(_canonical, "cancel_financial_transaction"):
    _canonical.cancel_financial_transaction = _canonical.cancel_appointment_transaction

    def _compat_cancel_appointment_transaction(*, appointment):
        return _canonical.cancel_financial_transaction(appointment=appointment)

    _canonical.cancel_appointment_transaction = _compat_cancel_appointment_transaction

sys.modules[__name__] = _canonical
