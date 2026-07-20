from __future__ import annotations

from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import Throttled, ValidationError

from apps.audit.services import log_access


def _audit(request, action: str, obj, event: str) -> None:
    log_access(request, action, obj=obj, obj_repr=f"{obj._meta.label}#{obj.pk} action={event}")


def _rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    cache_key = f"communications:rate:{key}"
    try:
        current = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window_seconds)
        current = 1
    if current > limit:
        raise Throttled(detail="Muitas tentativas. Aguarde e tente novamente.")


def _parse_period(request):
    end = timezone.now()
    start = end - timedelta(days=30)
    try:
        if request.query_params.get("start_date"):
            start = datetime.fromisoformat(request.query_params["start_date"])
            if timezone.is_naive(start):
                start = timezone.make_aware(start)
        if request.query_params.get("end_date"):
            end = datetime.fromisoformat(request.query_params["end_date"])
            if timezone.is_naive(end):
                end = timezone.make_aware(end)
    except ValueError as exc:
        raise ValidationError("Período inválido.") from exc
    if start >= end:
        raise ValidationError("A data inicial deve ser anterior à data final.")
    return start, end
