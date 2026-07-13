from importlib import import_module

from django.db import migrations


MODEL_ORDER = (
    "CommunicationTemplate",
    "CommunicationAutomation",
    "Communication",
    "CommunicationRecipient",
    "CommunicationAttempt",
    "CommunicationAutomationRun",
    "CommunicationPreference",
    "InAppNotification",
    "InboundMessage",
    "CommunicationChannelConfig",
    "PublicCommunicationActionToken",
    "CommunicationPlanEntitlement",
)


def _table_names(schema_editor):
    return set(schema_editor.connection.introspection.table_names())


def _table_columns(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(
            cursor,
            table_name,
        )
    return {column.name for column in description}


def _table_row_count(schema_editor, table_name):
    quoted_table = schema_editor.quote_name(table_name)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}")
        return cursor.fetchone()[0]


def _named_database_objects(schema_editor, table_name):
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(
            cursor,
            table_name,
        )
    return set(constraints)


def _field_can_be_added_to_populated_table(field):
    return bool(field.null or field.has_default())


def _add_missing_columns(schema_editor, model):
    table_name = model._meta.db_table
    actual_columns = _table_columns(schema_editor, table_name)
    missing_fields = [
        field
        for field in model._meta.local_fields
        if field.column is not None and field.column not in actual_columns
    ]
    if not missing_fields:
        return

    row_count = _table_row_count(schema_editor, table_name)
    for field in missing_fields:
        if row_count and not _field_can_be_added_to_populated_table(field):
            raise RuntimeError(
                f"A tabela {table_name!r} está incompleta e contém dados. "
                f"A coluna obrigatória {field.column!r} não pode ser criada "
                "automaticamente sem um valor padrão. Restaure um backup ou "
                "corrija essa coluna manualmente antes de executar as migrations."
            )
        schema_editor.add_field(model, field)


def _add_missing_named_objects(schema_editor, model):
    table_name = model._meta.db_table

    # No SQLite, add_constraint() pode reconstruir a tabela inteira. Durante essa
    # reconstrução, o Django também recria outras constraints e índices definidos
    # no estado do modelo. Por isso, a introspecção precisa ser atualizada antes de
    # cada operação; uma lista capturada uma única vez fica obsoleta e provoca
    # erros como "index ... already exists".
    for constraint in model._meta.constraints:
        if not constraint.name:
            continue
        existing_names = _named_database_objects(schema_editor, table_name)
        if constraint.name not in existing_names:
            schema_editor.add_constraint(model, constraint)

    for index in model._meta.indexes:
        if not index.name:
            continue
        existing_names = _named_database_objects(schema_editor, table_name)
        if index.name not in existing_names:
            schema_editor.add_index(model, index)


def reconcile_communications_schema(apps, schema_editor):
    existing_tables = _table_names(schema_editor)

    for model_name in MODEL_ORDER:
        model = apps.get_model("communications", model_name)
        table_name = model._meta.db_table

        if table_name not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(table_name)
            continue

        _add_missing_columns(schema_editor, model)
        _add_missing_named_objects(schema_editor, model)

    # As migrations antigas podem estar registradas como aplicadas mesmo quando
    # a execução foi interrompida antes dos seeds. As funções são idempotentes.
    seed_templates = import_module(
        "apps.communications.migrations.0006_seed_default_templates"
    ).seed_templates
    seed_entitlements = import_module(
        "apps.communications.migrations.0007_communication_plan_entitlements"
    ).seed_entitlements
    seed_templates(apps, schema_editor)
    seed_entitlements(apps, schema_editor)


def noop_reverse(apps, schema_editor):
    # A migration apenas reconcilia objetos que já deveriam existir segundo o
    # estado histórico. Reverter não deve remover tabelas ou dados válidos.
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0007_communication_plan_entitlements"),
    ]

    operations = [
        migrations.RunPython(reconcile_communications_schema, noop_reverse),
    ]
