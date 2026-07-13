from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.db import migrations

from apps.communications.migration_operations import CreateModelIfNotExists


class _Cursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _Introspection:
    def __init__(self, *, tables=(), columns=()):
        self._tables = list(tables)
        self._columns = list(columns)

    def table_names(self):
        return self._tables

    def get_table_description(self, cursor, table_name):
        return [SimpleNamespace(name=column) for column in self._columns]


class _Connection:
    alias = "default"

    def __init__(self, introspection):
        self.introspection = introspection

    def cursor(self):
        return _Cursor()


class _SchemaEditor:
    def __init__(self, *, tables=(), columns=()):
        self.connection = _Connection(
            _Introspection(tables=tables, columns=columns)
        )


def _model(*columns):
    return SimpleNamespace(
        _meta=SimpleNamespace(
            app_label="communications",
            model_name="example",
            db_table="communications_example",
            local_fields=[SimpleNamespace(column=column) for column in columns],
            can_migrate=lambda connection_alias: True,
        )
    )


def _state(model):
    return SimpleNamespace(
        apps=SimpleNamespace(get_model=lambda app_label, name: model)
    )


def test_create_model_if_not_exists_creates_missing_table():
    operation = CreateModelIfNotExists(name="Example", fields=[])
    model = _model("id", "name")
    state = _state(model)
    schema_editor = _SchemaEditor()

    with patch.object(
        migrations.CreateModel,
        "database_forwards",
    ) as create_model:
        operation.database_forwards(
            "communications",
            schema_editor,
            state,
            state,
        )

    create_model.assert_called_once_with(
        "communications",
        schema_editor,
        state,
        state,
    )


def test_create_model_if_not_exists_accepts_complete_existing_table():
    operation = CreateModelIfNotExists(name="Example", fields=[])
    model = _model("id", "name")
    state = _state(model)
    schema_editor = _SchemaEditor(
        tables=["communications_example"],
        columns=["id", "name"],
    )

    with patch.object(
        migrations.CreateModel,
        "database_forwards",
    ) as create_model:
        operation.database_forwards(
            "communications",
            schema_editor,
            state,
            state,
        )

    create_model.assert_not_called()


def test_create_model_if_not_exists_rejects_incomplete_existing_table():
    operation = CreateModelIfNotExists(name="Example", fields=[])
    model = _model("id", "name")
    state = _state(model)
    schema_editor = _SchemaEditor(
        tables=["communications_example"],
        columns=["id"],
    )

    with pytest.raises(RuntimeError, match="Colunas ausentes: name"):
        operation.database_forwards(
            "communications",
            schema_editor,
            state,
            state,
        )
