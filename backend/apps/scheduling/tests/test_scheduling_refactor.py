from django.apps import apps
from django.urls import resolve, reverse
from django.test import SimpleTestCase

from apps.agenda.models import Appointment as LegacyAppointment
from apps.scheduling.models import Appointment


class SchedulingRenameTests(SimpleTestCase):
    def test_package_name_changes_without_changing_app_label(self):
        config = apps.get_app_config("agenda")

        self.assertEqual(config.name, "apps.scheduling")
        self.assertEqual(config.label, "agenda")
        self.assertEqual(Appointment._meta.app_label, "agenda")
        self.assertIs(LegacyAppointment, Appointment)

    def test_database_tables_keep_historical_prefix(self):
        model_tables = {
            model._meta.db_table
            for model in apps.get_app_config("agenda").get_models()
        }

        self.assertTrue(model_tables)
        self.assertTrue(all(table.startswith("agenda_") for table in model_tables))
        self.assertFalse(any(table.startswith("scheduling_") for table in model_tables))

    def test_canonical_and_legacy_routes_share_the_same_view(self):
        canonical = resolve("/api/v1/scheduling/appointments/")
        legacy = resolve("/api/v1/agenda/appointments/")

        self.assertIs(canonical.func.cls, legacy.func.cls)
        self.assertTrue(reverse("appointment-list").startswith("/api/v1/scheduling/"))
