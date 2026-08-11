import importlib
import types
from unittest import mock

import pytest

migration = importlib.import_module(
    "apps.communications.migrations.0008_reconcile_runtime_schema"
)


class Cursor:
    def __init__(self, *, row_count=0):
        self.row_count = row_count

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, query):
        self.query = query

    def fetchone(self):
        return (self.row_count,)


class Introspection:
    def __init__(self, *, tables=(), columns=(), constraints=None):
        self.tables = list(tables)
        self.columns = list(columns)
        self.constraints = constraints or {}

    def table_names(self):
        return self.tables

    def get_table_description(self, cursor, table_name):
        return [types.SimpleNamespace(name=column) for column in self.columns]

    def get_constraints(self, cursor, table_name):
        return self.constraints


class Connection:
    alias = "default"

    def __init__(self, introspection, *, row_count=0):
        self.introspection = introspection
        self.row_count = row_count

    def cursor(self):
        return Cursor(row_count=self.row_count)


class SchemaEditor:
    def __init__(self, *, tables=(), columns=(), constraints=None, row_count=0):
        self.connection = Connection(
            Introspection(
                tables=tables,
                columns=columns,
                constraints=constraints,
            ),
            row_count=row_count,
        )
        self.create_model = mock.Mock()
        self.add_field = mock.Mock()
        self.add_constraint = mock.Mock()
        self.add_index = mock.Mock()

    @staticmethod
    def quote_name(name):
        return f'"{name}"'


def field(name, *, null=False, has_default=False):
    return types.SimpleNamespace(
        column=name,
        null=null,
        has_default=lambda: has_default,
    )


def model(*fields, constraints=(), indexes=()):
    return types.SimpleNamespace(
        _meta=types.SimpleNamespace(
            db_table="communications_example",
            local_fields=list(fields),
            constraints=list(constraints),
            indexes=list(indexes),
        )
    )


def apps_for(example_model):
    return types.SimpleNamespace(
        get_model=lambda app_label, model_name: example_model,
    )


def test_reconciliation_creates_missing_table_and_reseeds_data():
    example_model = model(field("id"))
    schema_editor = SchemaEditor()
    template_seed = mock.Mock()
    entitlement_seed = mock.Mock()

    with (
        mock.patch.object(migration, "MODEL_ORDER", ("Example",)),
        mock.patch.object(
            migration,
            "import_module",
            side_effect=[
                types.SimpleNamespace(seed_templates=template_seed),
                types.SimpleNamespace(seed_entitlements=entitlement_seed),
            ],
        ),
    ):
        migration.reconcile_communications_schema(
            apps_for(example_model),
            schema_editor,
        )

    schema_editor.create_model.assert_called_once_with(example_model)
    template_seed.assert_called_once()
    entitlement_seed.assert_called_once()


def test_reconciliation_adds_missing_column_to_empty_table():
    missing_field = field("name")
    example_model = model(field("id"), missing_field)
    schema_editor = SchemaEditor(
        tables=["communications_example"],
        columns=["id"],
        row_count=0,
    )

    migration._add_missing_columns(schema_editor, example_model)

    schema_editor.add_field.assert_called_once_with(example_model, missing_field)


def test_reconciliation_rejects_required_column_on_populated_table():
    missing_field = field("owner_id", null=False, has_default=False)
    example_model = model(field("id"), missing_field)
    schema_editor = SchemaEditor(
        tables=["communications_example"],
        columns=["id"],
        row_count=1,
    )

    with pytest.raises(RuntimeError, match="owner_id"):
        migration._add_missing_columns(schema_editor, example_model)

    schema_editor.add_field.assert_not_called()


def test_reconciliation_restores_named_constraints_and_indexes():
    constraint = types.SimpleNamespace(name="communications_example_unique")
    index = types.SimpleNamespace(name="communications_example_idx")
    example_model = model(
        field("id"),
        constraints=[constraint],
        indexes=[index],
    )
    schema_editor = SchemaEditor(
        tables=["communications_example"],
        columns=["id"],
        constraints={},
    )

    migration._add_missing_named_objects(schema_editor, example_model)

    schema_editor.add_constraint.assert_called_once_with(example_model, constraint)
    schema_editor.add_index.assert_called_once_with(example_model, index)


def test_reconciliation_refreshes_objects_after_sqlite_table_rebuild():
    first_constraint = types.SimpleNamespace(name="communications_example_unique")
    second_constraint = types.SimpleNamespace(name="communications_example_partial_unique")
    index = types.SimpleNamespace(name="communications_example_idx")
    example_model = model(
        field("id"),
        constraints=[first_constraint, second_constraint],
        indexes=[index],
    )
    schema_editor = SchemaEditor(
        tables=["communications_example"],
        columns=["id"],
        constraints={},
    )

    def simulate_sqlite_table_rebuild(model_instance, constraint):
        schema_editor.connection.introspection.constraints = {
            first_constraint.name: {},
            second_constraint.name: {},
            index.name: {},
        }

    schema_editor.add_constraint.side_effect = simulate_sqlite_table_rebuild

    migration._add_missing_named_objects(schema_editor, example_model)

    schema_editor.add_constraint.assert_called_once_with(example_model, first_constraint)
    schema_editor.add_index.assert_not_called()
