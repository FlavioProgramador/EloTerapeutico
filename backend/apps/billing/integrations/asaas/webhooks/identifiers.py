from __future__ import annotations

import hashlib
import json


def payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def event_id(payload: dict) -> str | None:
    explicit_id = payload.get("id") or payload.get("eventId")
    if explicit_id:
        return str(explicit_id)
    event_type = payload.get("event", "UNKNOWN")
    payment = payload.get("payment") or {}
    subscription = payload.get("subscription") or {}
    related_id = payment.get("id") or subscription.get("id")
    return f"{event_type}:{related_id}" if related_id else None
