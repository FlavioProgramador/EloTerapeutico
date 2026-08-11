from importlib import import_module
from pathlib import Path

from django.apps import apps
from django.test import SimpleTestCase
from django.urls import Resolver404, resolve, reverse

from apps.scheduling.models import Appointment


class SchedulingRenameTests(SimpleTestCase):
    def test_package_name_changes_without_changing_app_label(self):
        config = apps.get_app_config("agenda")

        self.assertEqual(config.name, "apps.scheduling")
        self.assertEqual(config.label, "agenda")
        self.assertEqual(Appointment._meta.app_label, "agenda")

    def test_legacy_python_package_is_removed(self):
        apps_root = Path(__file__).resolve().parents[2]

        self.assertFalse((apps_root / "agenda").exists())
        with self.assertRaises(ModuleNotFoundError):
            import_module("apps.agenda")

    def test_database_tables_keep_historical_prefix(self):
        model_tables = {
            model._meta.db_table
            for model in apps.get_app_config("agenda").get_models()
        }

        self.assertTrue(model_tables)
        self.assertTrue(all(table.startswith("agenda_") for table in model_tables))
        self.assertFalse(any(table.startswith("scheduling_") for table in model_tables))

    def test_only_canonical_route_is_registered(self):
        canonical = resolve("/api/v1/scheduling/appointments/")

        self.assertIsNotNone(canonical.func.cls)
        with self.assertRaises(Resolver404):
            resolve("/api/v1/agenda/appointments/")
        self.assertTrue(reverse("appointment-list").startswith("/api/v1/scheduling/"))
