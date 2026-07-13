from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import InAppNotification
from ..selectors import unread_notifications
from ..serializers import InAppNotificationSerializer
from ..services import notification_mark_read


class InAppNotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = InAppNotificationSerializer

    def get_queryset(self):
        queryset = InAppNotification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get("is_read") in {"true", "false"}:
            queryset = queryset.filter(is_read=self.request.query_params["is_read"] == "true")
        if self.request.query_params.get("priority"):
            queryset = queryset.filter(priority=self.request.query_params["priority"])
        return queryset

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        return Response(self.get_serializer(notification_mark_read(self.get_object())).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        updated = unread_notifications(request.user).update(is_read=True, read_at=timezone.now())
        return Response({"updated": updated})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        return Response({"count": unread_notifications(request.user).count()})
