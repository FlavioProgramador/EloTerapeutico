"""Orquestrador das validações arquiteturais do backend."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from apps.core.quality.legacy_backend_architecture import main as validate_existing_architecture
from apps.core.quality.rules import (
    validate_core_architecture,
    validate_documents_architecture,
)


def main() -> None:
    """Valida regras modulares e, em seguida, as regras legadas do backend."""

    errors: list[str] = []
    validate_core_architecture(errors)
    validate_documents_architecture(errors)
    if errors:
        raise SystemExit(
            "Falhas de arquitetura do backend:\n- " + "\n- ".join(sorted(set(errors)))
        )
    validate_existing_architecture()


if __name__ == "__main__":
    main()
