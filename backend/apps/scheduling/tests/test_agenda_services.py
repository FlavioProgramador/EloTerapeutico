from datetime import time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.agenda.models import Appointment, AppointmentRecurrence, Room, ScheduleBlock
from apps.agenda.selectors import available_slots
from apps.agenda.services import create_schedule_block, end_recurrence
from apps.patients.models import Patient
from apps.users.models import User, WorkingHours


class AgendaServiceLayerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="agenda-owner@example.test",
            password="strong-password",
            full_name="Profissional Agenda",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-agenda-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(full_name="Paciente Agenda", therapist=self.owner)
        self.other_patient = Patient.objects.create(full_name="Paciente Externo", therapist=self.other_owner)

    def test_end_recurrence_cancels_only_future_open_occurrences(self):
        today = timezone.localdate()
        recurrence = AppointmentRecurrence.objects.create(
            patient=self.patient,
            therapist=self.owner,
            frequency=AppointmentRecurrence.Frequency.WEEKLY,
            starts_on=today,
            start_time=time(10, 0),
            duration_minutes=50,
            session_value=Decimal("150.00"),
            created_by=self.owner,
        )
        start = timezone.now() + timedelta(days=7)
        future = Appointment.objects.create(
            patient=self.patient,
            therapist=self.owner,
            recurrence=recurrence,
            start_time=start,
            end_time=start + timedelta(minutes=50),
            session_value=Decimal("150.00"),
            status=Appointment.Status.SCHEDULED,
        )
        completed = Appointment.objects.create(
            patient=self.patient,
            therapist=self.owner,
            recurrence=recurrence,
            start_time=start + timedelta(hours=2),
            end_time=start + timedelta(hours=2, minutes=50),
            session_value=Decimal("150.00"),
            status=Appointment.Status.COMPLETED,
        )

        recurrence = end_recurrence(recurrence=recurrence, ends_on=today)
        future.refresh_from_db()
        completed.refresh_from_db()

        self.assertEqual(recurrence.status, AppointmentRecurrence.Status.ENDED)
        self.assertEqual(future.status, Appointment.Status.CANCELLED)
        self.assertEqual(future.cancellation_reason, "Recorrência encerrada.")
        self.assertEqual(completed.status, Appointment.Status.COMPLETED)

    def test_schedule_block_service_creates_recurrence_children_atomically(self):
        start = timezone.now() + timedelta(days=1)
        block = create_schedule_block(
            actor=self.owner,
            validated_data={
                "therapist": self.owner,
                "start_time": start,
                "end_time": start + timedelta(hours=1),
                "reason": ScheduleBlock.Reason.MEETING,
                "recurrence_rule": "weekly",
                "recurrence_count": 4,
            },
        )

        self.assertEqual(block.created_by, self.owner)
        self.assertEqual(block.occurrences.count(), 3)
        self.assertEqual(
            list(block.occurrences.order_by("start_time").values_list("start_time", flat=True)),
            [start + timedelta(weeks=index) for index in range(1, 4)],
        )

    def test_availability_selector_rejects_foreign_patient_and_room_relationships(self):
        target_date = timezone.localdate() + timedelta(days=2)
        WorkingHours.objects.create(
            therapist=self.owner,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        foreign_room = Room.objects.create(therapist=self.other_owner, name="Sala externa")

        with patch.object(
            Appointment,
            "conflict_details",
            return_value={"therapist": False, "patient": False, "room": False, "block": False},
        ) as conflict_details:
            slots = available_slots(
                therapist=self.owner,
                target_date=target_date,
                duration=30,
                patient_id=self.other_patient.pk,
                room_id=foreign_room.pk,
            )

        self.assertEqual(len(slots), 2)
        first_call = conflict_details.call_args_list[0].kwargs
        self.assertIsNone(first_call["patient"])
        self.assertIsNone(first_call["room"])
