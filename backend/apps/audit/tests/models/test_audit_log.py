import pytest

from apps.audit.exceptions import AuditLogImmutableError
from apps.audit.models import AuditLog


@pytest.fixture
def audit_log(db):
    return AuditLog.objects.create(
        action=AuditLog.Action.VIEW,
        object_repr="patients.Patient#1",
    )


def test_audit_log_preserves_historical_contract():
    assert AuditLog._meta.app_label == "audit"
    assert AuditLog._meta.db_table == "users_auditlog"
    assert AuditLog._meta.indexes[0].fields == ["user", "timestamp"]
    assert AuditLog._meta.indexes[1].fields == ["content_type", "object_id"]
    assert AuditLog._meta.ordering == ["-timestamp"]


@pytest.mark.django_db
def test_audit_log_allows_insert():
    entry = AuditLog.objects.create(
        action=AuditLog.Action.CREATE,
        object_repr="documents.GeneratedDocument#10",
    )
    assert entry.pk is not None


def test_instance_save_is_blocked(audit_log):
    audit_log.object_repr = "changed"
    with pytest.raises(AuditLogImmutableError):
        audit_log.save()


def test_instance_delete_is_blocked(audit_log):
    with pytest.raises(AuditLogImmutableError):
        audit_log.delete()


def test_queryset_update_is_blocked(audit_log):
    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.filter(pk=audit_log.pk).update(object_repr="changed")


def test_queryset_delete_is_blocked(audit_log):
    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.filter(pk=audit_log.pk).delete()


def test_bulk_update_is_blocked(audit_log):
    audit_log.object_repr = "changed"
    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.bulk_update([audit_log], ["object_repr"])


def test_update_or_create_is_blocked(db):
    with pytest.raises(AuditLogImmutableError):
        AuditLog.objects.update_or_create(
            object_repr="patients.Patient#1",
            defaults={"action": AuditLog.Action.UPDATE},
        )


def test_string_representation_does_not_include_user(audit_log):
    rendered = str(audit_log)
    assert audit_log.action in rendered
    assert audit_log.object_repr in rendered
