from __future__ import annotations

import shutil
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]

RECURSIVE_CACHE_DIRECTORIES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "htmlcov",
}

ROOT_GENERATED_DIRECTORIES = {
    "media",
    "staticfiles",
    "test-media",
    ".test-media",
    "venv",
    ".venv",
    "core",
    "elo_terapeutico",
}

ROOT_GENERATED_FILES = {
    ".coverage",
    "db.sqlite3",
    "test.sqlite3",
    "billing-ci.sqlite3",
    "backend-root-cleanup.sqlite3",
}


def remove_directory(path: Path, removed: list[str]) -> None:
    if not path.is_dir():
        return
    shutil.rmtree(path, ignore_errors=False)
    removed.append(str(path.relative_to(BACKEND)))


def main() -> None:
    removed: list[str] = []

    for path in sorted(BACKEND.rglob("*"), reverse=True):
        if path.is_dir() and path.name in RECURSIVE_CACHE_DIRECTORIES:
            remove_directory(path, removed)

    for directory_name in ROOT_GENERATED_DIRECTORIES:
        remove_directory(BACKEND / directory_name, removed)

    for filename in ROOT_GENERATED_FILES:
        path = BACKEND / filename
        if path.is_file():
            path.unlink()
            removed.append(filename)

    if removed:
        print("Removidos:")
        for item in sorted(set(removed)):
            print(f"- {item}")
    else:
        print("Nenhum resíduo local encontrado.")


if __name__ == "__main__":
    main()
