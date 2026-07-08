import os
import re
from pathlib import Path

BACKEND_DIR = Path("d:/Projetos/elo-terapeutico/backend")
APP_DIR = BACKEND_DIR / "apps" / "patients"

(APP_DIR / "api" / "views").mkdir(parents=True, exist_ok=True)
(APP_DIR / "api" / "serializers").mkdir(parents=True, exist_ok=True)
(APP_DIR / "services").mkdir(parents=True, exist_ok=True)
(APP_DIR / "selectors").mkdir(parents=True, exist_ok=True)

MOVES = {
    "dashboard_queries.py": "selectors/dashboard_queries.py",
    "dashboard_serializers.py": "api/serializers/dashboard_serializers.py",
    "detail_serializers.py": "api/serializers/detail_serializers.py",
    "form_serializers.py": "api/serializers/form_serializers.py",
    "list_serializers.py": "api/serializers/list_serializers.py",
    "workspace_serializers.py": "api/serializers/workspace_serializers.py",
    "professional_serializers.py": "api/serializers/professional_serializers.py",
    "patient_professionals.py": "api/serializers/patient_professionals.py",
    "review_filter.py": "api/review_filter.py",
    "reminder_view.py": "api/views/reminder_view.py",
    "permissions.py": "services/access_control.py",
    "api/serializers.py": "api/serializers/legacy_serializers.py",
    "api/views.py": "api/views/legacy_views.py",
    "api/patient_viewset.py": "api/views/patient_viewset.py",
    "api/dashboard_actions.py": "api/views/dashboard_actions.py",
    "api/export_actions.py": "api/views/export_actions.py",
}

DELETIONS = [
    "api/dashboard_queries.py",
    "api/form_serializers.py",
    "api/list_serializers.py",
    "api/reminder_view.py",
    "filters.py",
    "views.py",
    "serializers.py",
]

for d in ["api/views", "api/serializers", "services", "selectors"]:
    init_file = APP_DIR / d / "__init__.py"
    if not init_file.exists():
        init_file.touch()

IMPORT_REPLACEMENTS = {
    r"apps\.patients\.dashboard_queries": r"apps.patients.selectors.dashboard_queries",
    r"apps\.patients\.dashboard_serializers": r"apps.patients.api.serializers.dashboard_serializers",
    r"apps\.patients\.detail_serializers": r"apps.patients.api.serializers.detail_serializers",
    r"apps\.patients\.form_serializers": r"apps.patients.api.serializers.form_serializers",
    r"apps\.patients\.list_serializers": r"apps.patients.api.serializers.list_serializers",
    r"apps\.patients\.workspace_serializers": r"apps.patients.api.serializers.workspace_serializers",
    r"apps\.patients\.professional_serializers": r"apps.patients.api.serializers.professional_serializers",
    r"apps\.patients\.patient_professionals": r"apps.patients.api.serializers.patient_professionals",
    r"apps\.patients\.reminder_view": r"apps.patients.api.views.reminder_view",
    r"apps\.patients\.review_filter": r"apps.patients.api.review_filter",
    r"apps\.patients\.permissions": r"apps.patients.services.access_control",
    r"apps\.patients\.api\.serializers(?!\.)": r"apps.patients.api.serializers.legacy_serializers",
    r"apps\.patients\.api\.views(?!\.)": r"apps.patients.api.views.legacy_views",
    r"apps\.patients\.api\.patient_viewset": r"apps.patients.api.views.patient_viewset",
    r"apps\.patients\.api\.dashboard_actions": r"apps.patients.api.views.dashboard_actions",
    r"apps\.patients\.api\.export_actions": r"apps.patients.api.views.export_actions",
}

for del_file in DELETIONS:
    p = APP_DIR / del_file
    if p.exists():
        p.unlink()

for src, dst in MOVES.items():
    src_path = APP_DIR / src
    dst_path = APP_DIR / dst
    if src_path.exists():
        os.rename(src_path, dst_path)

for py_file in BACKEND_DIR.rglob("*.py"):
    if ".venv" in py_file.parts or "venv" in py_file.parts:
        continue
    try:
        content = py_file.read_text(encoding="utf-8")
        original_content = content
        
        for pattern, replacement in IMPORT_REPLACEMENTS.items():
            content = re.sub(pattern, replacement, content)
            
        if "apps" in py_file.parts and "patients" in py_file.parts:
            content = re.sub(r'from \.\.permissions import', r'from apps.patients.services.access_control import', content)
            content = re.sub(r'from \.\.selectors\.patients import', r'from apps.patients.selectors.patients import', content)
            content = re.sub(r'from \.dashboard_actions import', r'from apps.patients.api.views.dashboard_actions import', content)
            content = re.sub(r'from \.export_actions import', r'from apps.patients.api.views.export_actions import', content)
            content = re.sub(r'from \.patient_viewset import', r'from apps.patients.api.views.patient_viewset import', content)
            content = re.sub(r'from \.dashboard_queries import', r'from apps.patients.selectors.dashboard_queries import', content)
            content = re.sub(r'from \.form_serializers import', r'from apps.patients.api.serializers.form_serializers import', content)
            content = re.sub(r'from \.list_serializers import', r'from apps.patients.api.serializers.list_serializers import', content)
            content = re.sub(r'from \.reminder_view import', r'from apps.patients.api.views.reminder_view import', content)
            content = re.sub(r'from \.serializers import', r'from apps.patients.api.serializers.legacy_serializers import', content)
            content = re.sub(r'from \.patient_professionals import', r'from apps.patients.api.serializers.patient_professionals import', content)
            content = re.sub(r'from \.dashboard_serializers import', r'from apps.patients.api.serializers.dashboard_serializers import', content)
            content = re.sub(r'from \.detail_serializers import', r'from apps.patients.api.serializers.detail_serializers import', content)
            content = re.sub(r'from \.workspace_serializers import', r'from apps.patients.api.serializers.workspace_serializers import', content)
            content = re.sub(r'from \.professional_serializers import', r'from apps.patients.api.serializers.professional_serializers import', content)
            content = re.sub(r'from \.review_filter import', r'from apps.patients.api.review_filter import', content)
            content = re.sub(r'from \.permissions import', r'from apps.patients.services.access_control import', content)
            
            # Since some files were at root and are now in api/serializers/, their from .models import Patient must become apps.patients.models
            content = re.sub(r'from \.models import', r'from apps.patients.models import', content)

        if content != original_content:
            py_file.write_text(content, encoding="utf-8")
    except Exception:
        pass

print("Done organizing patients app.")
