from django.conf import settings


def test_celery_uses_separate_queues():
    queue_names = {queue.name for queue in settings.CELERY_TASK_QUEUES}

    assert {"default", "exports", "communications"}.issubset(queue_names)


def test_celery_routes_sensitive_work_to_expected_queues():
    assert settings.CELERY_TASK_ROUTES["apps.records.tasks.*"]["queue"] == "exports"
    assert settings.CELERY_TASK_ROUTES["apps.communications.tasks.*"]["queue"] == "communications"
    assert settings.CELERY_TASK_ROUTES["apps.billing.tasks.*"]["queue"] == "default"
