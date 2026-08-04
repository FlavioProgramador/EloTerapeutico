import { Field, SectionLabel, Toggle, fieldClass } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentOptionsSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
}

import { useId } from "react";

export function AppointmentOptionsSection({
  form,
  setForm,
  disabled,
}: AppointmentOptionsSectionProps & { disabled?: boolean }) {
  const baseId = useId();
  const reminderToggleId = `${baseId}-reminder`;
  const recurringToggleId = `${baseId}-recurring`;
  const frequencySelectId = `${baseId}-frequency`;
  const occurrencesInputId = `${baseId}-occurrences`;
  const endsOnInputId = `${baseId}-ends-on`;
  const conflictSelectId = `${baseId}-conflict`;

  return (
    <section className="space-y-3">
      <SectionLabel>Opções</SectionLabel>
      <Toggle
        id={reminderToggleId}
        checked={form.reminder}
        onChange={(value) =>
          setForm((current) => ({ ...current, reminder: value }))
        }
        label="Enviar lembrete automático via WhatsApp"
        description="O envio fica registrado na fila de lembretes."
        disabled={disabled}
      />
      <Toggle
        id={recurringToggleId}
        checked={form.recurring}
        onChange={(value) =>
          setForm((current) => ({ ...current, recurring: value }))
        }
        label="Consulta recorrente"
        description="Cria sessões repetidas e permite edição por escopo."
        disabled={disabled}
      />
      {form.recurring && (
        <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Frequência" htmlFor={frequencySelectId}>
              <select
                id={frequencySelectId}
                value={form.frequency}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    frequency: event.target
                      .value as AppointmentFormState["frequency"],
                  }))
                }
                className={fieldClass}
                disabled={disabled}
              >
                <option value="weekly">Semanal</option>
                <option value="biweekly">Quinzenal</option>
                <option value="monthly">Mensal</option>
              </select>
            </Field>
            <Field label="Quantidade" htmlFor={occurrencesInputId}>
              <input
                id={occurrencesInputId}
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
                disabled={disabled}
              />
            </Field>
          </div>
          <Field label="Encerrar em (opcional)" htmlFor={endsOnInputId}>
            <input
              id={endsOnInputId}
              type="date"
              value={form.endsOn}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  endsOn: event.target.value,
                }))
              }
              className={fieldClass}
              disabled={disabled}
            />
          </Field>
          <Field label="Quando houver conflito" htmlFor={conflictSelectId}>
            <select
              id={conflictSelectId}
              value={form.conflictStrategy}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  conflictStrategy: event.target
                    .value as AppointmentFormState["conflictStrategy"],
                }))
              }
              className={fieldClass}
              disabled={disabled}
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
