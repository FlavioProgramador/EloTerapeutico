from __future__ import annotations

import hashlib
import secrets

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Communication
from .common import _rate_limit


class CommunicationWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def post(self, request, provider):
        _rate_limit(f"webhook:{provider}", limit=240, window_seconds=60)
        if provider != "whatsapp" or not getattr(settings, "WHATSAPP_PROVIDER", ""):
            return Response({"status": "disabled", "message": "Provedor não configurado."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        configured_token = getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        supplied_token = request.headers.get("X-Webhook-Token", "")
        if not configured_token or not secrets.compare_digest(configured_token, supplied_token):
            return Response({"status": "invalid"}, status=status.HTTP_401_UNAUTHORIZED)
        payload = request.data if isinstance(request.data, dict) else {}
        event_id = str(payload.get("event_id", ""))[:160]
        provider_message_id = str(payload.get("provider_message_id", ""))[:160]
        provider_status = str(payload.get("status", "")).lower()
        if not event_id or not provider_message_id or provider_status not in {"sent", "delivered", "read", "failed"}:
            return Response({"status": "invalid"}, status=status.HTTP_400_BAD_REQUEST)
        event_fingerprint = hashlib.sha256(f"{provider}:{event_id}".encode()).hexdigest()
        if not cache.add(f"communications:webhook:{event_fingerprint}", True, timeout=7 * 24 * 60 * 60):
            return Response({"status": "duplicate"})
        communication = Communication.objects.filter(channel=Communication.Channel.WHATSAPP, provider_message_id=provider_message_id).first()
        if communication is None:
            return Response({"status": "ignored"})
        now = timezone.now()
        update_fields = ["status", "updated_at"]
        if provider_status == "sent":
            communication.status = Communication.Status.SENT
            communication.sent_at = communication.sent_at or now
            update_fields.append("sent_at")
        elif provider_status == "delivered":
            communication.status = Communication.Status.DELIVERED
            communication.delivered_at = now
            update_fields.append("delivered_at")
        elif provider_status == "read":
            communication.status = Communication.Status.READ
            communication.read_at = now
            update_fields.append("read_at")
        else:
            communication.status = Communication.Status.FAILED
            communication.failed_at = now
            update_fields.append("failed_at")
        communication.save(update_fields=update_fields)
        return Response({"status": "processed"})
