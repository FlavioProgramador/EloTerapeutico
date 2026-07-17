from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.communications.models import (
    CommunicationAutomation,
    CommunicationAutomationRun,
)

from .base import ReadOnlyHistoryAdmin


@admin.register(CommunicationAutomation)
class CommunicationAutomationAdmin(ModelAdmin):
    list_display = (
        "name",
        "owner",
        "event_type",
        "channel",
        "template",
        "is_active",
        "updated_at",
    )
    list_filter = ("event_type", "channel", "is_active")
    search_fields = ("name", "description", "owner__email")
    list_select_related = ("owner", "template", "created_by", "updated_by")


@admin.register(CommunicationAutomationRun)
class CommunicationAutomationRunAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "automation",
        "source_event",
        "status",
        "communication",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "source_event", "started_at")
    search_fields = ("automation__name", "source_object_id", "idempotency_key")
    readonly_fields = tuple(
        field.name for field in CommunicationAutomationRun._meta.fields
    )
    list_select_related = ("automation", "communication")
