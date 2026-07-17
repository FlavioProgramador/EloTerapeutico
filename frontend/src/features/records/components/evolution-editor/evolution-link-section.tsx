import { CalendarDays, Link2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { EvolutionEditorController } from "../../hooks/use-evolution-editor-controller";
import {
  evolutionFieldClass,
  formatAppointmentOption,
  formatEvolutionDate,
} from "./evolution-editor.utils";

export function EvolutionLinkSection({
  controller,
}: {
  controller: EvolutionEditorController;
}) {
  return (
    <>
      <section className="space-y-2">
        <label
          htmlFor="evolution-appointment"
          className="flex items-center gap-2 text-xs font-semibold text-foreground"
        >
          <Link2 className="size-4 text-muted-foreground" />
          Vincular a Consulta
        </label>
        <select
          id="evolution-appointment"
          value={controller.form.appointment}
          onChange={(event) =>
            controller.selectAppointment(event.target.value)
          }
          disabled={controller.busy || controller.appointmentQuery.isLoading}
          className={evolutionFieldClass}
        >
          <option value="">
            {controller.appointmentQuery.isLoading
              ? "Carregando consultas..."
              : "Sem vínculo"}
          </option>
          {controller.appointmentOptions.map((appointment) => (
            <option key={appointment.id} value={appointment.id}>
              {formatAppointmentOption(appointment)}
            </option>
          ))}
        </select>
        <p className="text-[11px] text-muted-foreground">
          Vincule esta evolução a uma consulta específica do paciente.
        </p>
        {controller.appointmentQuery.isError && (
          <p role="alert" className="text-[11px] text-destructive">
            Não foi possível carregar as consultas. O registro ainda pode ser
            criado sem vínculo.
          </p>
        )}
      </section>

      <section className="space-y-2">
        <label
          htmlFor="evolution-session-date"
          className="flex items-center gap-2 text-xs font-semibold text-foreground"
        >
          <CalendarDays className="size-4 text-muted-foreground" />
          Data do Atendimento
        </label>
        <input
          id="evolution-session-date"
          type="date"
          value={controller.form.sessionDate}
          max={controller.todayDate}
          onChange={(event) => {
            controller.changeForm("sessionDate", event.target.value);
            controller.setForm((current) => ({
              ...current,
              dateOverrideConfirmed: false,
            }));
          }}
          disabled={controller.busy}
          required
          aria-invalid={Boolean(controller.errors.sessionDate)}
          aria-describedby={
            controller.errors.sessionDate
              ? "evolution-session-date-error"
              : undefined
          }
          className={cn(
            evolutionFieldClass,
            controller.errors.sessionDate && "border-destructive",
          )}
        />
        {controller.dateDiffersFromAppointment && (
          <label className="flex items-start gap-2 rounded-md border border-amber-500/25 bg-amber-500/10 p-3 text-[11px] text-foreground">
            <input
              type="checkbox"
              checked={controller.form.dateOverrideConfirmed}
              onChange={(event) =>
                controller.changeForm(
                  "dateOverrideConfirmed",
                  event.target.checked,
                )
              }
              disabled={controller.busy}
              className="mt-0.5"
            />
            Confirmo que a data informada difere da consulta vinculada (
            {controller.linkedAppointmentDate
              ? formatEvolutionDate(
                  `${controller.linkedAppointmentDate}T12:00:00`,
                )
              : "data não disponível"}
            ).
          </label>
        )}
        {controller.errors.sessionDate && (
          <p
            id="evolution-session-date-error"
            role="alert"
            className="text-[11px] text-destructive"
          >
            {controller.errors.sessionDate}
          </p>
        )}
      </section>
    </>
  );
}
