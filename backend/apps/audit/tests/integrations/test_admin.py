import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory

from apps.audit.admin.audit_logs import AuditLogAdmin
from apps.audit.models import AuditLog
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
def test_admin_is_strictly_read_only():
    user = _user("audit-admin-readonly@teste.com", superuser=True)
    request = RequestFactory().get("/admin/audit/auditlog/")
    request.user = user
    model_admin = AuditLogAdmin(AuditLog, admin.site)
    assert model_admin.has_add_permission(request) is False
    assert model_admin.has_change_permission(request) is False
    assert model_admin.has_delete_permission(request) is False
    assert model_admin.has_view_permission(request) is True


@pytest.mark.django_db
def test_admin_requires_explicit_view_permission():
    user = _user("audit-admin-denied@teste.com")
    request = RequestFactory().get("/admin/audit/auditlog/")
    request.user = user
    model_admin = AuditLogAdmin(AuditLog, admin.site)
    assert model_admin.has_view_permission(request) is False
    user.user_permissions.add(Permission.objects.get(codename="view_auditlog"))
    assert model_admin.has_view_permission(request) is True
