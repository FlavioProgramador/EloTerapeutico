"""Casos de uso de bloqueios de agenda."""

from datetime import timedelta

from django.db import transaction

from apps.scheduling.models import ScheduleBlock


@transaction.atomic
def create_schedule_block(*, actor, validated_data: dict) -> ScheduleBlock:
    recurrence_count = validated_data.pop("recurrence_count", 4)
    validated_data["created_by"] = actor
    block = ScheduleBlock.objects.create(**validated_data)
    delta = {
        "weekly": timedelta(weeks=1),
        "biweekly": timedelta(weeks=2),
    }.get(block.recurrence_rule)
    if delta:
        ScheduleBlock.objects.bulk_create(
            [
                ScheduleBlock(
                    therapist=block.therapist,
                    start_time=block.start_time + delta * index,
                    end_time=block.end_time + delta * index,
                    reason=block.reason,
                    notes=block.notes,
                    recurrence_rule=block.recurrence_rule,
                    parent_block=block,
                    created_by=block.created_by,
                )
                for index in range(1, recurrence_count)
            ]
        )
    return block
