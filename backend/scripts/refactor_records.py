import os
import re
from pathlib import Path

BACKEND_DIR = Path("d:/Projetos/elo-terapeutico/backend")
RECORDS_DIR = BACKEND_DIR / "apps" / "records"

# Create target directories
(RECORDS_DIR / "api" / "views").mkdir(parents=True, exist_ok=True)
(RECORDS_DIR / "api" / "serializers").mkdir(parents=True, exist_ok=True)
(RECORDS_DIR / "services").mkdir(parents=True, exist_ok=True)
(RECORDS_DIR / "models").mkdir(parents=True, exist_ok=True)

# Define moves
MOVES = {
    # Views
    "clinical_views.py": "api/views/clinical_views.py",
    "secure_document_views.py": "api/views/secure_document_views.py",
    "finalize_views.py": "api/views/finalize_views.py",
    "views.py": "api/views/legacy_views.py", # Rename to avoid conflict with api/views package? No, let's keep it views.py or rename to legacy_views.py. Let's use legacy_views.py
    
    # Serializers
    "clinical_serializers.py": "api/serializers/clinical_serializers.py",
    "evolution_flow_serializers.py": "api/serializers/evolution_flow_serializers.py",
    "serializers.py": "api/serializers/legacy_serializers.py",
    
    # Services
    "utils.py": "services/utils.py",
    "evolution_security.py": "services/evolution_security.py",
    
    # Models
    "evolution_flow_models.py": "models/templates.py",
}

# Add __init__.py
for d in ["api/views", "api/serializers", "services"]:
    init_file = RECORDS_DIR / d / "__init__.py"
    if not init_file.exists():
        init_file.touch()

# Mapping for import replacements
IMPORT_REPLACEMENTS = {
    r"apps\.records\.clinical_views": r"apps.records.api.views.clinical_views",
    r"apps\.records\.secure_document_views": r"apps.records.api.views.secure_document_views",
    r"apps\.records\.finalize_views": r"apps.records.api.views.finalize_views",
    r"apps\.records\.views": r"apps.records.api.views.legacy_views",
    
    r"apps\.records\.clinical_serializers": r"apps.records.api.serializers.clinical_serializers",
    r"apps\.records\.evolution_flow_serializers": r"apps.records.api.serializers.evolution_flow_serializers",
    r"apps\.records\.serializers": r"apps.records.api.serializers.legacy_serializers",
    
    r"apps\.records\.utils": r"apps.records.services.utils",
    r"apps\.records\.evolution_security": r"apps.records.services.evolution_security",
    
    r"apps\.records\.evolution_flow_models": r"apps.records.models.templates",
}

# 1. Move files
for src, dst in MOVES.items():
    src_path = RECORDS_DIR / src
    dst_path = RECORDS_DIR / dst
    if src_path.exists():
        os.rename(src_path, dst_path)
        print(f"Moved {src} to {dst}")

# 2. Update imports in all python files in backend
for py_file in BACKEND_DIR.rglob("*.py"):
    if ".venv" in py_file.parts or "venv" in py_file.parts:
        continue
    
    try:
        content = py_file.read_text(encoding="utf-8")
        original_content = content
        
        # Absolute imports
        for pattern, replacement in IMPORT_REPLACEMENTS.items():
            content = re.sub(pattern, replacement, content)
            
        # Relative imports inside apps/records
        if "apps" in py_file.parts and "records" in py_file.parts:
            # We need to be careful with relative imports. 
            # A simpler way is to let Ruff fix relative imports or we can replace them explicitly.
            # Example: from .clinical_views import -> from .api.views.clinical_views import
            rel_replacements = {
                r"from \.clinical_views": r"from .api.views.clinical_views",
                r"from \.secure_document_views": r"from .api.views.secure_document_views",
                r"from \.finalize_views": r"from .api.views.finalize_views",
                r"from \.views": r"from .api.views.legacy_views",
                
                r"from \.clinical_serializers": r"from .api.serializers.clinical_serializers",
                r"from \.evolution_flow_serializers": r"from .api.serializers.evolution_flow_serializers",
                r"from \.serializers": r"from .api.serializers.legacy_serializers",
                
                r"from \.utils": r"from .services.utils",
                r"from \.evolution_security": r"from .services.evolution_security",
                r"from \.evolution_flow_models": r"from .models.templates",
            }
            # Also handle intra-directory relative imports if we moved them.
            # Like if clinical_views imports clinical_serializers: from .clinical_serializers -> from ..serializers.clinical_serializers
            # Let's do absolute replacements inside records to be safe
            for rel_pat, rel_repl in rel_replacements.items():
                content = re.sub(rel_pat, rel_repl, content)
        
        if content != original_content:
            py_file.write_text(content, encoding="utf-8")
            print(f"Updated imports in {py_file.relative_to(BACKEND_DIR)}")
    except Exception as e:
        print(f"Error processing {py_file}: {e}")

print("Done organizing records app.")
