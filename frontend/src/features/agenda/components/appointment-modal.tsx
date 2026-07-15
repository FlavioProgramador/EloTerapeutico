"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Clock3, Repeat2, Users, Video } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { useAuth } from "@/contexts/auth";
import {
  usePatientProfessionals,
  usePatients,
} from "@/features/patients/hooks/use-patients";
import {
  useAvailableSlots,
  useCreateAppointment,
  useRooms,
} from "../hooks/use-agenda";
import { toDateInput } from "../lib/calendar.mjs";
import type {
  AppointmentModality,
  AppointmentType,
  CreateAppointmentPayload,
} from "../types";
import { Field, SectionLabel, Toggle, fieldClass } from "./agenda-ui";

interface AppointmentForm {
  patient: string;
  therapist: string;
  date: string;
  time: string;
  duration: string;
  modality: AppointmentModality;
  appointmentType: AppointmentType;
  room: string;
  sessionValue: string;
  notes: string;
  reminder: boolean;
  recurring: boolean;
  frequency: "weekly" | "biweekly" | "monthly" | "custom";
  occurrences: string;
  endsOn: string;
  conflictStrategy: "error" | "skip";
}

function initialForm(
  date: Date,
  time: string,
  userId?: number,
): AppointmentForm {
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

export function AppointmentModal({
  open,
  defaultDate,
  defaultTime = "09:00",
  onClose,
}: {
  open: boolean;
  defaultDate: Date;
  defaultTime?: string;
  onClose: () => void;
}) {
  const { user } = useAuth();
  const createMutation = useCreateAppointment();
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<AppointmentForm>(() =>
    initialForm(defaultDate, defaultTime, user?.id),
  );
  const { data: patientsPage } = usePatients({
    status: "active",
    search: search || undefined,
    page_size: 100,
  });
  const { data: professionals = [] } = usePatientProfessionals();
  const { data: rooms = [] } = useRooms();
  const patients = patientsPage?.results || [];
  const duration = Number(form.duration || 50);
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
    setForm(initialForm(defaultDate, defaultTime, user?.id));
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

  const endTime = useMemo(() => {
    const start = new Date(`${form.date}T${form.time}:00`);
    return new Date(start.getTime() + duration * 60_000);
  }, [form.date, form.time, duration]);

  function applySlot(value: string) {
    const slot = slots.find((item) => item.start_datetime === value);
    if (!slot) return;
    const date = new Date(slot.start_datetime);
    setForm((current) => ({
      ...current,
      date: toDateInput(date),
      time: date.toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
    }));
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const start = new Date(`${form.date}T${form.time}:00`);
    if (!form.patient || !form.therapist || Number.isNaN(start.getTime()))
      return;

    const payload: CreateAppointmentPayload = {
      patient: Number(form.patient),
      therapist: Number(form.therapist),
      start_time: start.toISOString(),
      end_time: endTime.toISOString(),
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
    createMutation.mutate(payload, { onSuccess: onClose });
  }

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Nova consulta"
      description="Todos os campos essenciais em uma única tela."
      className="max-w-4xl"
    >
      <form onSubmit={submit} className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-5">
          <section className="space-y-3">
            <SectionLabel>Quem e quando</SectionLabel>
            <Field label="Buscar paciente">
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Nome, telefone, e-mail ou CPF..."
                className={fieldClass}
              />
            </Field>
            <Field label="Paciente *">
              <select
                value={form.patient}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    patient: event.target.value,
                  }))
                }
                className={fieldClass}
                required
              >
                <option value="">Selecione o paciente</option>
                {patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.social_name || patient.full_name}
                  </option>
                ))}
              </select>
            </Field>
            {(user?.role === "admin" || user?.role === "secretary") && (
              <Field label="Profissional responsável *">
                <select
                  value={form.therapist}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      therapist: event.target.value,
                    }))
                  }
                  className={fieldClass}
                  required
                >
                  <option value="">Selecione</option>
                  {professionals.map((professional) => (
                    <option key={professional.id} value={professional.id}>
                      {professional.full_name}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            <div className="grid grid-cols-2 gap-3">
              <Field label="Data *">
                <input
                  type="date"
                  value={form.date}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      date: event.target.value,
                    }))
                  }
                  className={fieldClass}
                  required
                />
              </Field>
              <Field label="Horário *">
                <input
                  type="time"
                  value={form.time}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      time: event.target.value,
                    }))
                  }
                  className={fieldClass}
                  required
                />
              </Field>
            </div>
            <Field label="Horários livres sugeridos">
              <select
                onChange={(event) => applySlot(event.target.value)}
                className={fieldClass}
                defaultValue=""
              >
                <option value="">
                  {loadingSlots
                    ? "Buscando disponibilidade..."
                    : slots.length
                      ? "Selecione um horário livre"
                      : "Nenhum horário livre encontrado"}
                </option>
                {slots.map((slot) => (
                  <option key={slot.start_datetime} value={slot.start_datetime}>
                    {slot.start}–{slot.end}
                  </option>
                ))}
              </select>
            </Field>
          </section>

          <section className="space-y-3 border-t border-border pt-4">
            <SectionLabel>Detalhes</SectionLabel>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Duração">
                <select
                  value={form.duration}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      duration: event.target.value,
                    }))
                  }
                  className={fieldClass}
                >
                  {[30, 45, 50, 60, 90, 120].map((value) => (
                    <option key={value} value={value}>
                      {value} min
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Tipo">
                <select
                  value={form.appointmentType}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      appointmentType: event.target.value as AppointmentType,
                    }))
                  }
                  className={fieldClass}
                >
                  <option value="assessment">Avaliação</option>
                  <option value="psychotherapy">Psicoterapia</option>
                  <option value="follow_up">Retorno</option>
                  <option value="guidance">Orientação</option>
                  <option value="group">Sessão em grupo</option>
                  <option value="other">Outro</option>
                </select>
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Modalidade">
                <select
                  value={form.modality}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      modality: event.target.value as AppointmentModality,
                      room: event.target.value === "online" ? "" : current.room,
                    }))
                  }
                  className={fieldClass}
                >
                  <option value="in_person">Presencial</option>
                  <option value="online">Online</option>
                  <option value="hybrid">Híbrida</option>
                </select>
              </Field>
              <Field label="Sala">
                <select
                  value={form.room}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      room: event.target.value,
                    }))
                  }
                  className={fieldClass}
                  disabled={form.modality === "online"}
                >
                  <option value="">Sem sala</option>
                  {rooms.map((room) => (
                    <option key={room.id} value={room.id}>
                      {room.name}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Field label="Valor (R$)">
              <input
                inputMode="decimal"
                value={form.sessionValue}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    sessionValue: event.target.value.replace(",", "."),
                  }))
                }
                className={fieldClass}
              />
            </Field>
          </section>
        </div>

        <div className="space-y-5">
          <section className="space-y-3">
            <SectionLabel>Opções</SectionLabel>
            <Toggle
              checked={form.reminder}
              onChange={(value) =>
                setForm((current) => ({ ...current, reminder: value }))
              }
              label="Enviar lembrete automático via WhatsApp"
              description="O envio fica registrado na fila de lembretes."
            />
            <Toggle
              checked={form.recurring}
              onChange={(value) =>
                setForm((current) => ({ ...current, recurring: value }))
              }
              label="Consulta recorrente"
              description="Cria sessões repetidas e permite edição por escopo."
            />
            {form.recurring && (
              <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
                <div className="grid grid-cols-2 gap-3">
                  <Field label="Frequência">
                    <select
                      value={form.frequency}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          frequency: event.target
                            .value as AppointmentForm["frequency"],
                        }))
                      }
                      className={fieldClass}
                    >
                      <option value="weekly">Semanal</option>
                      <option value="biweekly">Quinzenal</option>
                      <option value="monthly">Mensal</option>
                    </select>
                  </Field>
                  <Field label="Quantidade">
                    <input
                      type="number"
                      min={2}
                      max={365}
                      value={form.occurrences}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          occurrences: event.target.value,
                        }))
                      }
                      className={fieldClass}
                    />
                  </Field>
                </div>
                <Field label="Encerrar em (opcional)">
                  <input
                    type="date"
                    value={form.endsOn}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        endsOn: event.target.value,
                      }))
                    }
                    className={fieldClass}
                  />
                </Field>
                <Field label="Quando houver conflito">
                  <select
                    value={form.conflictStrategy}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        conflictStrategy: event.target
                          .value as AppointmentForm["conflictStrategy"],
                      }))
                    }
                    className={fieldClass}
                  >
                    <option value="error">Interromper e informar</option>
                    <option value="skip">
                      Pular apenas a ocorrência conflitante
                    </option>
                  </select>
                </Field>
              </div>
            )}
          </section>

          <section className="space-y-3 border-t border-border pt-4">
            <SectionLabel>Observações administrativas</SectionLabel>
            <textarea
              value={form.notes}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
              rows={6}
              placeholder="Informações operacionais sobre a consulta..."
              className="w-full rounded-md border border-border bg-background p-3 text-sm outline-none focus:border-primary"
            />
          </section>

          <div className="rounded-xl border border-border bg-secondary/15 p-4 text-xs text-muted-foreground">
            <p className="flex items-center gap-2 font-semibold text-foreground">
              {form.modality === "online" ? (
                <Video className="size-4 text-primary" />
              ) : form.recurring ? (
                <Repeat2 className="size-4 text-primary" />
              ) : form.appointmentType === "group" ? (
                <Users className="size-4 text-primary" />
              ) : (
                <CalendarDays className="size-4 text-primary" />
              )}
              Resumo do agendamento
            </p>
            <p className="mt-2 flex items-center gap-2">
              <Clock3 className="size-3.5" />
              {form.date} · {form.time} · {duration} minutos
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-border pt-4 lg:col-span-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={createMutation.isPending}>
            Agendar consulta
          </Button>
        </div>
      </form>
    </Modal>
  );
}
