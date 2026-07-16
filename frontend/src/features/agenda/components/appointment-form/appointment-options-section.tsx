import { Field, SectionLabel, Toggle, fieldClass } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentOptionsSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
}

export function AppointmentOptionsSection({
  form,
  setForm,
}: AppointmentOptionsSectionProps) {
  return (
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
