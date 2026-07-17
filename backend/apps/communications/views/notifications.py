from __future__ import annotations

from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog

from ..models import InAppNotification
from ..serializers import InAppNotificationSerializer, NotificationPreferenceSerializer
from ..services import (
    get_notification_preferences,
    notification_archive,
    notification_mark_read,
    notification_mark_unread,
)
from .common import _audit, _rate_limit


class InAppNotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = InAppNotificationSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_queryset(self):
        now = timezone.now()
        queryset = InAppNotification.objects.filter(recipient=self.request.user).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )
        archived = self.request.query_params.get("archived")
        if archived == "true":
            queryset = queryset.filter(archived_at__isnull=False)
        elif archived != "all":
            queryset = queryset.filter(archived_at__isnull=True)
        is_read = self.request.query_params.get("is_read")
        if is_read in {"true", "false"}:
            queryset = queryset.filter(is_read=is_read == "true")
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        priority = self.request.query_params.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(message__icontains=search))
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        ordering = self.request.query_params.get("ordering", "-created_at")
        if ordering not in {"created_at", "-created_at", "priority", "-priority"}:
            ordering = "-created_at"
        return queryset.order_by(ordering)

    @action(detail=True, methods=["post"])
    def read(self, request, public_id=None):
        notification = notification_mark_read(self.get_object())
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def unread(self, request, public_id=None):
        notification = notification_mark_unread(self.get_object())
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, public_id=None):
        notification = notification_archive(self.get_object())
        _audit(request, AuditLog.Action.UPDATE, notification, "notification_archived")
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        _rate_limit(f"notifications:read-all:{request.user.pk}", limit=20, window_seconds=60)
        updated = self.get_queryset().filter(is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"updated": updated})

    @action(detail=False, methods=["post"], url_path="archive-read")
    def archive_read(self, request):
        _rate_limit(f"notifications:archive-read:{request.user.pk}", limit=10, window_seconds=60)
        updated = self.get_queryset().filter(is_read=True).update(archived_at=timezone.now())
        return Response({"updated": updated})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"count": count})

    @action(detail=False, methods=["get"], url_path="categories")
    def categories(self, request):
        return Response(
            [
                {"value": value, "label": label}
                for value, label in InAppNotification.Category.choices
            ]
        )


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        preference = get_notification_preferences(request.user)
        return Response(NotificationPreferenceSerializer(preference).data)

    def patch(self, request):
        preference = get_notification_preferences(request.user)
        serializer = NotificationPreferenceSerializer(
            preference,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        preference = serializer.save()
        _audit(request, AuditLog.Action.UPDATE, preference, "notification_preferences_updated")
        return Response(NotificationPreferenceSerializer(preference).data, status=status.HTTP_200_OK)
