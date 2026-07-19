"""Admin de salas, bloqueios e sessões vinculadas."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.scheduling.models import PackageSession, Room, ScheduleBlock


@admin.register(ScheduleBlock)
class ScheduleBlockAdmin(ModelAdmin):
    list_display = (
        "id",
        "therapist",
        "start_time",
        "end_time",
        "reason",
        "is_active",
    )
    list_filter = ("reason", "is_active", "therapist")
    search_fields = ("therapist__full_name", "therapist__email", "notes")
    list_select_related = ("therapist",)
    autocomplete_fields = ("therapist",)
    date_hierarchy = "start_time"


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ("name", "therapist", "location", "capacity", "is_active")
    list_filter = ("is_active", "therapist")
    search_fields = ("name", "location", "therapist__full_name")
    list_select_related = ("therapist",)
    autocomplete_fields = ("therapist",)


@admin.register(PackageSession)
class PackageSessionAdmin(ModelAdmin):
    list_display = (
        "package",
        "appointment",
        "scheduled_for",
        "status",
        "consumed",
    )
    list_filter = ("status", "consumed", "scheduled_for")
    search_fields = ("package__name", "appointment__patient__full_name")
    list_select_related = ("package", "appointment")
    raw_id_fields = ("appointment",)


__all__ = ["PackageSessionAdmin", "RoomAdmin", "ScheduleBlockAdmin"]
