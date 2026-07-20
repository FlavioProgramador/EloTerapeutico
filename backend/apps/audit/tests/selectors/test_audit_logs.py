import pytest
from django.contrib.auth.models import Permission

from apps.audit.models import AuditLog
from apps.audit.selectors import audit_logs_accessible_to, audit_logs_for_action
from apps.users.models import User


def _user(email: str, *, superuser: bool = False) -> User:
    if superuser:
        return User.objects.create_superuser(
            email=email,
            full_name="Audit Admin",
            password="TestPass2026!_audit",
        )
    return User.objects.create_user(
        email=email,
        full_name="Audit User",
        password="TestPass2026!_audit",
    )


@pytest.mark.django_db
def test_superuser_can_access_audit_logs():
    admin = _user("audit-admin@teste.com", superuser=True)
    AuditLog.objects.create(action=AuditLog.Action.VIEW, object_repr="patients.Patient#1")
    assert audit_logs_accessible_to(user=admin).count() == 1


@pytest.mark.django_db
def test_user_with_explicit_permission_can_access():
    user = _user("audit-permission@teste.com")
    user.user_permissions.add(Permission.objects.get(codename="view_auditlog"))
    AuditLog.objects.create(action=AuditLog.Action.UPDATE, object_repr="users.User#1")
    assert audit_logs_accessible_to(user=user).count() == 1


@pytest.mark.django_db
def test_regular_user_cannot_access_global_audit():
    user = _user("audit-regular@teste.com")
    AuditLog.objects.create(action=AuditLog.Action.VIEW, object_repr="patients.Patient#1")
    assert audit_logs_accessible_to(user=user).count() == 0


@pytest.mark.django_db
def test_action_selector_reuses_authorized_scope():
    admin = _user("audit-filter@teste.com", superuser=True)
    AuditLog.objects.create(action=AuditLog.Action.VIEW, object_repr="patients.Patient#1")
    AuditLog.objects.create(action=AuditLog.Action.UPDATE, object_repr="patients.Patient#1")
    assert audit_logs_for_action(user=admin, action=AuditLog.Action.VIEW).count() == 1
