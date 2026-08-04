import { CalendarDays, Clock3, Repeat2, Users, Video } from "lucide-react";

import { SectionLabel } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentAdministrativeSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
  duration: number;
}

import { useId } from "react";

export function AppointmentAdministrativeSection({
  form,
  setForm,
  duration,
  disabled,
}: AppointmentAdministrativeSectionProps & { disabled?: boolean }) {
  const baseId = useId();
  const notesTextareaId = `${baseId}-notes-textarea`;

  return (
    <>
      <section className="space-y-3 border-t border-border pt-4">
        <label htmlFor={notesTextareaId} className="block">
          <SectionLabel>Observações administrativas</SectionLabel>
        </label>
        <textarea
          id={notesTextareaId}
          value={form.notes}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              notes: event.target.value,
            }))
          }
          rows={6}
          placeholder="Informações operacionais sobre a consulta..."
          className="w-full rounded-md border border-border bg-background p-3 text-sm outline-none transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={disabled}
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
    </>
  );
}
