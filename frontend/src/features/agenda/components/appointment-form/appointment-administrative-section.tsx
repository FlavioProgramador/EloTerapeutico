import { useId } from "react";
import { CalendarDays, Clock3, Repeat2, Users, Video } from "lucide-react";

import { Field, SectionLabel } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentAdministrativeSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
  duration: number;
  isSubmitting?: boolean;
}

export function AppointmentAdministrativeSection({
  form,
  setForm,
  duration,
  isSubmitting = false,
}: AppointmentAdministrativeSectionProps) {
  const notesId = useId();

  return (
    <>
      <section className="space-y-3 border-t border-border pt-4">
        <SectionLabel>Observações administrativas</SectionLabel>
        <Field label="" htmlFor={notesId}>
          <textarea
            id={notesId}
            value={form.notes}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                notes: event.target.value,
              }))
            }
            rows={6}
            placeholder="Informações operacionais sobre a consulta..."
            className="w-full rounded-md border border-border bg-background p-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
          />
        </Field>
      </section>

      <div className="rounded-xl border border-border bg-secondary/15 p-4 text-xs text-muted-foreground">
        <p className="flex items-center gap-2 font-semibold text-foreground">
          {form.modality === "online" ? (
            <Video className="size-4 text-primary" aria-hidden="true" />
          ) : form.recurring ? (
            <Repeat2 className="size-4 text-primary" aria-hidden="true" />
          ) : form.appointmentType === "group" ? (
            <Users className="size-4 text-primary" aria-hidden="true" />
          ) : (
            <CalendarDays className="size-4 text-primary" aria-hidden="true" />
          )}
          Resumo do agendamento
        </p>
        <p className="mt-2 flex items-center gap-2">
          <Clock3 className="size-3.5" aria-hidden="true" />
          {form.date} · {form.time} · {duration} minutos
        </p>
      </div>
    </>
  );
}
