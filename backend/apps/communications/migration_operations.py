from __future__ import annotations

from django.db import migrations


class CreateModelIfNotExists(migrations.CreateModel):
    """Create a model table only when it is absent from the database.

    This keeps the migration state deterministic while recovering databases
    where a previous interrupted migration created the table without recording
    the migration as applied.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.name)
        if not self.allow_migrate_model(schema_editor.connection.alias, model):
            return None

        table_name = model._meta.db_table
        if table_name not in self._table_names(schema_editor):
            return super().database_forwards(
                app_label,
                schema_editor,
                from_state,
                to_state,
            )

        self._validate_existing_table(schema_editor, model)
        return None

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        model = from_state.apps.get_model(app_label, self.name)
        if not self.allow_migrate_model(schema_editor.connection.alias, model):
            return None
        if model._meta.db_table not in self._table_names(schema_editor):
            return None
        return super().database_backwards(
            app_label,
            schema_editor,
            from_state,
            to_state,
        )

    @staticmethod
    def _table_names(schema_editor) -> set[str]:
        return set(schema_editor.connection.introspection.table_names())

    @staticmethod
    def _validate_existing_table(schema_editor, model) -> None:
        table_name = model._meta.db_table
        with schema_editor.connection.cursor() as cursor:
            description = schema_editor.connection.introspection.get_table_description(
                cursor,
                table_name,
            )

        actual_columns = {column.name for column in description}
        expected_columns = {
            field.column
            for field in model._meta.local_fields
            if field.column is not None
        }
        missing_columns = sorted(expected_columns - actual_columns)
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise RuntimeError(
                f"A tabela existente {table_name!r} está incompleta. "
                f"Colunas ausentes: {missing}. "
                "Restaure o backup ou remova somente essa tabela parcial antes "
                "de executar as migrations novamente."
            )
