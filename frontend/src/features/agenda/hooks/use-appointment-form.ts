import type { FormEvent } from "react";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/contexts/auth";
import {
  usePatientProfessionals,
  usePatients,
} from "@/features/patients/hooks/use-patients";
import {
  appointmentTimeFromSlot,
  buildAppointmentPayload,
  calculateAppointmentEndTime,
  createInitialAppointmentForm,
} from "../components/appointment-form/appointment-form.utils";
import type { AppointmentFormState } from "../components/appointment-form/appointment-form.types";
import {
  useAvailableSlots,
  useCreateAppointment,
  useRooms,
} from "./use-agenda";

interface UseAppointmentFormOptions {
  open: boolean;
  defaultDate: Date;
  defaultTime: string;
  onSuccess: () => void;
}

export function useAppointmentForm({
  open,
  defaultDate,
  defaultTime,
  onSuccess,
}: UseAppointmentFormOptions) {
  const { user } = useAuth();
  const createMutation = useCreateAppointment();
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<AppointmentFormState>(() =>
    createInitialAppointmentForm(defaultDate, defaultTime, user?.id),
  );

  const { data: patientsPage } = usePatients({
    status: "active",
    search: search || undefined,
    page_size: 100,
  });
  const { data: professionals = [] } = usePatientProfessionals();
  const { data: rooms = [] } = useRooms();
  const patients = patientsPage?.results ?? [];
  const duration = Number(form.duration || 50);
  const endTime = useMemo(() => calculateAppointmentEndTime(form), [form]);

  const { data: slots = [], isLoading: loadingSlots } = useAvailableSlots(
    {
      date: form.date,
      duration,
      therapist_id: form.therapist ? Number(form.therapist) : undefined,
      patient_id: form.patient ? Number(form.patient) : undefined,
      room_id: form.room ? Number(form.room) : undefined,
    },
    open && Boolean(form.patient && form.date && form.therapist),
  );

  useEffect(() => {
    if (!open) return;
    setForm(createInitialAppointmentForm(defaultDate, defaultTime, user?.id));
    setSearch("");
  }, [open, defaultDate, defaultTime, user?.id]);

  useEffect(() => {
    const selected = patients.find(
      (patient) => patient.id === Number(form.patient),
    );
    if (!selected) return;

    setForm((current) => ({
      ...current,
      therapist:
        user?.role === "therapist"
          ? String(user.id)
          : String(selected.therapist || current.therapist),
      sessionValue: selected.session_value || current.sessionValue,
      modality:
        selected.modality === "online" || selected.modality === "hybrid"
          ? selected.modality
          : current.modality,
    }));
  }, [form.patient, patients, user]);

  function applySlot(value: string) {
    const slot = slots.find((item) => item.start_datetime === value);
    if (!slot) return;
    const appointmentTime = appointmentTimeFromSlot(slot.start_datetime);
    setForm((current) => ({ ...current, ...appointmentTime }));
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = buildAppointmentPayload(form);
    if (!payload) return;
    createMutation.mutate(payload, { onSuccess });
  }

  return {
    form,
    setForm,
    search,
    setSearch,
    patients,
    professionals,
    rooms,
    slots,
    loadingSlots,
    duration,
    endTime,
    showTherapistField:
      user?.role === "admin" || user?.role === "secretary",
    applySlot,
    submit,
    isSubmitting: createMutation.isPending,
  };
}
