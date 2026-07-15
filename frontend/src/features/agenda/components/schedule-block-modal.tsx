"use client";

import { useEffect, useMemo, useState } from "react";
import { LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { useAuth } from "@/contexts/auth";
import { usePatientProfessionals } from "@/features/patients/hooks/use-patients";
import { useCreateScheduleBlock } from "../hooks/use-agenda";
import { toDateInput } from "../lib/calendar.mjs";

const fieldClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15";

export function ScheduleBlockModal({
  open,
  defaultDate,
  onClose,
}: {
  open: boolean;
  defaultDate: Date;
  onClose: () => void;
}) {
  const { user } = useAuth();
  const { data: professionals = [] } = usePatientProfessionals();
  const createMutation = useCreateScheduleBlock();
  const [form, setForm] = useState({
    therapist: String(user?.id || ""),
    date: toDateInput(defaultDate),
    start: "12:00",
    end: "13:00",
    reason: "lunch",
    notes: "",
    recurrence: "",
    confirmConflicts: false,
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setForm({
      therapist: String(user?.id || ""),
      date: toDateInput(defaultDate),
      start: "12:00",
      end: "13:00",
      reason: "lunch",
      notes: "",
      recurrence: "",
      confirmConflicts: false,
    });
    setError("");
  }, [open, defaultDate, user?.id]);

  const interval = useMemo(() => {
    const start = new Date(`${form.date}T${form.start}:00`);
    const end = new Date(`${form.date}T${form.end}:00`);
    return { start, end, valid: end > start };
  }, [form.date, form.start, form.end]);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!interval.valid) {
      setError("O horário final deve ser posterior ao inicial.");
      return;
    }
    createMutation.mutate(
      {
        therapist: form.therapist ? Number(form.therapist) : undefined,
        start_time: interval.start.toISOString(),
        end_time: interval.end.toISOString(),
        reason: form.reason,
        notes: form.notes,
        recurrence_rule: form.recurrence,
        confirm_conflicts: form.confirmConflicts,
      },
      { onSuccess: onClose },
    );
  }

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Bloquear horário"
      description="Crie indisponibilidades sem cancelar consultas automaticamente."
      className="max-w-lg"
    >
      <form onSubmit={submit} className="space-y-4" noValidate>
        <div className="flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
          <LockKeyhole className="size-4 text-primary" />
          Consultas existentes serão preservadas. O sistema pedirá confirmação
          quando houver impacto.
        </div>

        {(user?.role === "admin" || user?.role === "secretary") && (
          <Field label="Profissional">
            <select
              value={form.therapist}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  therapist: event.target.value,
                }))
              }
              className={fieldClass}
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

        <Field label="Data">
          <input
            type="date"
            value={form.date}
            onChange={(event) =>
              setForm((current) => ({ ...current, date: event.target.value }))
            }
            className={fieldClass}
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Início">
            <input
              type="time"
              value={form.start}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  start: event.target.value,
                }))
              }
              className={fieldClass}
            />
          </Field>
          <Field label="Fim">
            <input
              type="time"
              value={form.end}
              onChange={(event) =>
                setForm((current) => ({ ...current, end: event.target.value }))
              }
              className={fieldClass}
            />
          </Field>
        </div>

        <Field label="Motivo">
          <select
            value={form.reason}
            onChange={(event) =>
              setForm((current) => ({ ...current, reason: event.target.value }))
            }
            className={fieldClass}
          >
            <option value="lunch">Almoço</option>
            <option value="meeting">Reunião</option>
            <option value="vacation">Férias</option>
            <option value="external">Atendimento externo</option>
            <option value="appointment">Compromisso</option>
            <option value="other">Outro</option>
          </select>
        </Field>

        <Field label="Recorrência do bloqueio">
          <select
            value={form.recurrence}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                recurrence: event.target.value,
              }))
            }
            className={fieldClass}
          >
            <option value="">Não repetir</option>
            <option value="weekly">Semanal</option>
            <option value="biweekly">Quinzenal</option>
          </select>
        </Field>

        <Field label="Motivo complementar (opcional)">
          <input
            value={form.notes}
            onChange={(event) =>
              setForm((current) => ({ ...current, notes: event.target.value }))
            }
            placeholder="Ex.: reunião de equipe, férias..."
            className={fieldClass}
          />
        </Field>

        <label className="flex items-start gap-2 rounded-lg border border-border bg-secondary/20 p-3 text-xs">
          <input
            type="checkbox"
            checked={form.confirmConflicts}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                confirmConflicts: event.target.checked,
              }))
            }
            className="mt-0.5"
          />
          <span>
            Confirmo a criação mesmo que existam consultas no intervalo. Nenhuma
            consulta será cancelada automaticamente.
          </span>
        </label>

        {error && (
          <p role="alert" className="text-xs font-medium text-destructive">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={createMutation.isPending}>
            Bloquear
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-semibold">{label}</span>
      {children}
    </label>
  );
}
