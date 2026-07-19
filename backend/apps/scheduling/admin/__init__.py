"""Registros administrativos do domínio de scheduling."""

from . import appointments as appointments
from . import packages as packages
from . import recurrences as recurrences
from . import resources as resources
from . import telemedicine as telemedicine

__all__ = [
    "appointments",
    "packages",
    "recurrences",
    "resources",
    "telemedicine",
]
