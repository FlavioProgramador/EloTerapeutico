from pathlib import Path

from django.apps import apps

BACKEND = Path(__file__).resolve().parents[3]
PROJECT_ROOT = BACKEND.parent


def test_only_canonical_core_package_exists():
    assert not (PROJECT_ROOT / "core").exists()
    assert not (BACKEND / "core").exists()
    assert (BACKEND / "apps" / "core").is_dir()


def test_old_django_configuration_package_was_removed():
    assert not (BACKEND / "elo_terapeutico").exists()
    assert (BACKEND / "config" / "settings" / "base.py").is_file()


def test_core_app_is_registered_once_with_preserved_label():
    configs = [config for config in apps.get_app_configs() if config.label == "core"]
    assert len(configs) == 1
    assert configs[0].name == "apps.core"
