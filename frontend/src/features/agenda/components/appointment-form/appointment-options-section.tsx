import { useId } from "react";
import { Field, SectionLabel, Toggle, fieldClass } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentOptionsSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
  disabled?: boolean;
}

export function AppointmentOptionsSection({
  form,
  setForm,
  disabled,
}: AppointmentOptionsSectionProps) {
  const baseId = useId();
  const reminderId = `${baseId}-reminder`;
  const recurringId = `${baseId}-recurring`;
  const frequencyId = `${baseId}-frequency`;
  const occurrencesId = `${baseId}-occurrences`;
  const endsOnId = `${baseId}-ends-on`;
  const conflictStrategyId = `${baseId}-conflict-strategy`;

  return (
    <section className="space-y-3">
      <SectionLabel>Opções</SectionLabel>
      <Toggle
        id={reminderId}
        checked={form.reminder}
        disabled={disabled}
        onChange={(value) =>
          setForm((current) => ({ ...current, reminder: value }))
        }
        label="Enviar lembrete automático via WhatsApp"
        description="O envio fica registrado na fila de lembretes."
      />
      <Toggle
        id={recurringId}
        checked={form.recurring}
        disabled={disabled}
        onChange={(value) =>
          setForm((current) => ({ ...current, recurring: value }))
        }
        label="Consulta recorrente"
        description="Cria sessões repetidas e permite edição por escopo."
      />
      {form.recurring && (
        <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Frequência" htmlFor={frequencyId}>
              <select
                id={frequencyId}
                value={form.frequency}
                disabled={disabled}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    frequency: event.target
                      .value as AppointmentFormState["frequency"],
                  }))
                }
                className={fieldClass}
              >
                <option value="weekly">Semanal</option>
                <option value="biweekly">Quinzenal</option>
                <option value="monthly">Mensal</option>
              </select>
            </Field>
            <Field label="Quantidade" htmlFor={occurrencesId}>
              <input
                id={occurrencesId}
                type="number"
                min={2}
                max={365}
                value={form.occurrences}
                disabled={disabled}
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
          <Field label="Encerrar em (opcional)" htmlFor={endsOnId}>
            <input
              id={endsOnId}
              type="date"
              value={form.endsOn}
              disabled={disabled}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  endsOn: event.target.value,
                }))
              }
              className={fieldClass}
            />
          </Field>
          <Field label="Quando houver conflito" htmlFor={conflictStrategyId}>
            <select
              id={conflictStrategyId}
              value={form.conflictStrategy}
              disabled={disabled}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  conflictStrategy: event.target
                    .value as AppointmentFormState["conflictStrategy"],
                }))
              }
              className={fieldClass}
            >
              <option value="error">Interromper e informar</option>
              <option value="skip">Pular apenas a ocorrência conflitante</option>
            </select>
          </Field>
        </div>
      )}
    </section>
  );
}
