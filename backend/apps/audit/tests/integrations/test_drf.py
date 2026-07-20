from types import SimpleNamespace

from apps.audit.integrations import AuditLogMixin
from apps.audit.models import AuditLog


class _BaseView:
    def __init__(self):
        self.request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True))
        self.action = "create"
        self.get_object_calls = 0
        self.persist_calls = 0

    def get_object(self):
        self.get_object_calls += 1
        return SimpleNamespace(
            pk=1,
            _meta=SimpleNamespace(label="patients.Patient"),
        )

    def get_serializer(self, instance):
        return SimpleNamespace(data={"id": instance.pk})

    def perform_create(self, serializer):
        self.persist_calls += 1
        serializer.instance = SimpleNamespace(
            pk=1,
            _meta=SimpleNamespace(label="patients.Patient"),
        )

    def perform_update(self, serializer):
        self.persist_calls += 1

    def perform_destroy(self, instance):
        self.persist_calls += 1
        instance.pk = None


class _View(AuditLogMixin, _BaseView):
    pass


def test_retrieve_gets_object_only_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "apps.audit.integrations.drf.record_audit_event",
        lambda **kwargs: calls.append(kwargs),
    )
    view = _View()
    response = view.retrieve(view.request)
    assert response.data == {"id": 1}
    assert view.get_object_calls == 1
    assert len(calls) == 1
    assert calls[0]["action"] == AuditLog.Action.VIEW


def test_perform_create_persists_and_audits_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "apps.audit.integrations.drf.record_audit_event",
        lambda **kwargs: calls.append(kwargs),
    )
    view = _View()
    serializer = SimpleNamespace(instance=None)
    view.perform_create(serializer)
    assert view.persist_calls == 1
    assert len(calls) == 1
    assert calls[0]["on_commit"] is True


def test_destroy_uses_snapshot_before_pk_is_cleared(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "apps.audit.integrations.drf.record_audit_event",
        lambda **kwargs: calls.append(kwargs),
    )
    view = _View()
    instance = view.get_object()
    view.perform_destroy(instance)
    assert view.persist_calls == 1
    assert calls[0]["resource_id"] == 1
    assert calls[0]["resource_label"] == "patients.Patient"
