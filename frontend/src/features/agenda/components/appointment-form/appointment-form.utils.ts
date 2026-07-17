import { toDateInput } from "../../lib/calendar.mjs";
import type { CreateAppointmentPayload } from "../../types";
import type { AppointmentFormState } from "./appointment-form.types";

export function createInitialAppointmentForm(
  date: Date,
  time: string,
  userId?: number,
): AppointmentFormState {
  return {
    patient: "",
    therapist: String(userId || ""),
    date: toDateInput(date),
    time,
    duration: "50",
    modality: "in_person",
    appointmentType: "psychotherapy",
    room: "",
    sessionValue: "0.00",
    notes: "",
    reminder: true,
    recurring: false,
    frequency: "weekly",
    occurrences: "4",
    endsOn: "",
    conflictStrategy: "error",
  };
}

export function calculateAppointmentEndTime(form: AppointmentFormState) {
  const start = new Date(`${form.date}T${form.time}:00`);
  const duration = Number(form.duration || 50);
  return new Date(start.getTime() + duration * 60_000);
}

export function buildAppointmentPayload(
  form: AppointmentFormState,
): CreateAppointmentPayload | null {
  const start = new Date(`${form.date}T${form.time}:00`);
  if (!form.patient || !form.therapist || Number.isNaN(start.getTime())) {
    return null;
  }

  const end = calculateAppointmentEndTime(form);
  return {
    patient: Number(form.patient),
    therapist: Number(form.therapist),
    start_time: start.toISOString(),
    end_time: end.toISOString(),
    modality: form.modality,
    appointment_type: form.appointmentType,
    room: form.modality === "online" || !form.room ? null : Number(form.room),
    session_value: Number(form.sessionValue || 0).toFixed(2),
    notes: form.notes,
    send_whatsapp_reminder: form.reminder,
    is_recurring: form.recurring,
    recurrence_frequency: form.recurring ? form.frequency : undefined,
    recurrence_max_occurrences: form.recurring
      ? Number(form.occurrences || 4)
      : undefined,
    recurrence_ends_on:
      form.recurring && form.endsOn ? form.endsOn : undefined,
    recurrence_conflict_strategy: form.conflictStrategy,
  };
}

export function appointmentTimeFromSlot(startDatetime: string) {
  const date = new Date(startDatetime);
  return {
    date: toDateInput(date),
    time: date.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }),
  };
}
