"""Admin do módulo de prontuários.

As classes foram separadas em `admin_parts/` por responsabilidade para manter
este arquivo apenas como ponto de carregamento do Django Admin.
"""

from .admin_parts import (  # noqa: F401
    AnamnesisAdmin,
    EvolutionAddendumAdmin,
    EvolutionAdmin,
)
