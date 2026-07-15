from unittest.mock import patch

from apps.communications.tasks import dispatch_due_communications


@patch("apps.communications.tasks.send_communication.apply_async")
@patch("apps.communications.tasks.claim_due_communications", return_value=[11, 12])
def test_dispatch_due_communications_publishes_only_identifiers(claim, apply_async):
    published = dispatch_due_communications.run()

    assert published == 2
    assert apply_async.call_count == 2
    apply_async.assert_any_call(args=[11], queue="communications")
    apply_async.assert_any_call(args=[12], queue="communications")
