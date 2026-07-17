from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from apps.billing.selectors.payments import get_payments_for_user

BILLING_ROOT = Path(__file__).resolve().parents[1]


def test_billing_views_delegate_external_integrations_and_queries():
    view_directories = [
        BILLING_ROOT / "api" / "v1" / "views",
        BILLING_ROOT / "api" / "public",
    ]
    checked_files = []

    for directory in view_directories:
        for path in directory.glob("*.py"):
            checked_files.append(path)
            source = path.read_text(encoding="utf-8")
            assert "from infrastructure." not in source, path
            assert "import infrastructure." not in source, path
            assert "apps.billing.infrastructure" not in source, path
            assert ".objects" not in source, path

    assert checked_files


def test_payment_selector_always_scopes_queries_to_user():
    user = SimpleNamespace(pk=37)
    filtered = Mock()
    selected = Mock()
    ordered = Mock()
    filtered.select_related.return_value = selected
    selected.order_by.return_value = ordered

    with patch("apps.billing.selectors.payments.Payment.objects") as manager:
        manager.filter.return_value = filtered
        result = get_payments_for_user(user=user)

    manager.filter.assert_called_once_with(user_id=37)
    filtered.select_related.assert_called_once_with(
        "billing_order",
        "subscription",
    )
    selected.order_by.assert_called_once_with(
        "due_date",
        "installment_number",
    )
    assert result is ordered
