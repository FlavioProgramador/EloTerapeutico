from celery import shared_task

from apps.scheduling.services.telemedicine import expire_telemedicine_rooms


@shared_task(
    name="apps.scheduling.tasks.expire_stale_telemedicine_rooms",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def expire_stale_telemedicine_rooms(self, batch_size: int = 100) -> int:
    del self
    return expire_telemedicine_rooms(batch_size=batch_size)
