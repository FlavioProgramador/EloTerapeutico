from pathlib import Path

from apps.core.quality.rules.audit import validate_audit_architecture


def test_audit_architecture_rule_passes_for_current_tree():
    errors: list[str] = []
    validate_audit_architecture(errors)
    assert errors == []


def test_audit_root_has_only_configuration_files():
    audit_root = Path(__file__).resolve().parents[2]
    files = {path.name for path in audit_root.iterdir() if path.is_file()}
    assert files == {"README.md", "__init__.py", "apps.py"}
