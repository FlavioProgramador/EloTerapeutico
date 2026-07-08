import os
import shutil
from pathlib import Path

backend_dir = Path(r"d:\Projetos\elo-terapeutico\backend")

core_dir = backend_dir / "core"
apps_core_dir = backend_dir / "apps" / "core"

# 1. Remove os arquivos antigos do core
for item in core_dir.iterdir():
    if item.is_file() and item.name.endswith(".py"):
        item.unlink()

# 2. Mover arquivos de apps/core para core (se já não estiverem lá)
if apps_core_dir.exists():
    for item in apps_core_dir.iterdir():
        if item.name == "__pycache__":
            shutil.rmtree(item)
            continue
        shutil.move(str(item), str(core_dir))
    shutil.rmtree(apps_core_dir)

# 3. Mover integrações
infra_dir = backend_dir / "infrastructure"
infra_dir.mkdir(exist_ok=True)
integrations_dir = core_dir / "integrations"
if integrations_dir.exists():
    for item in integrations_dir.iterdir():
        shutil.move(str(item), str(infra_dir))
    shutil.rmtree(integrations_dir)

(infra_dir / "__init__.py").write_text("")
