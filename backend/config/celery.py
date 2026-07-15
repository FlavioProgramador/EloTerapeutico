"""Aplicação Celery do Elo Terapêutico."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("elo_terapeutico")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True, name="config.celery.debug_task")
def debug_task(self):
    return {"task_id": self.request.id}
