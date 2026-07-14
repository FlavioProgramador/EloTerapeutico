"""Períodos e paginação compartilhados entre relatórios."""

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any

from django.utils import timezone


def safe_int(value: str | None, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def resolve_period(params) -> tuple[date, date]:
    today = timezone.localdate()
    custom_start = parse_iso_date(params.get("start_date"))
    custom_end = parse_iso_date(params.get("end_date"))
    if custom_start and custom_end:
        if custom_start > custom_end:
            raise ValueError("Data inicial maior que a data final.")
        return custom_start, custom_end

    period = params.get("period") or "this_month"
    if period == "today":
        return today, today
    if period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if period == "last_30_days":
        return today - timedelta(days=30), today
    if period == "last_90_days":
        return today - timedelta(days=90), today
    if period == "this_year":
        return date(today.year, 1, 1), today

    start = date(today.year, today.month, 1)
    end = date(today.year, today.month, monthrange(today.year, today.month)[1])
    return start, end


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def iter_months(start: date, end: date):
    current = month_start(start)
    limit = month_start(end)
    while current <= limit:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def month_key(value: date | datetime) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return f"{value.year:04d}-{value.month:02d}"


def label_month(value: date | datetime) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%m/%Y")


def page_queryset(queryset, params) -> dict[str, Any]:
    page = safe_int(params.get("page"), 1, 1, 10_000)
    page_size = safe_int(params.get("page_size"), 25, 1, 100)
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return {"count": total, "page": page, "page_size": page_size, "items": queryset[start:end]}
