import type { AgendaRoom, AppointmentModality, AppointmentType } from "../../types";
import { Field, SectionLabel, fieldClass } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentDetailsSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
  rooms: AgendaRoom[];
}

import { useId } from "react";

export function AppointmentDetailsSection({
  form,
  setForm,
  rooms,
  disabled,
}: AppointmentDetailsSectionProps & { disabled?: boolean }) {
  const baseId = useId();
  const durationSelectId = `${baseId}-duration`;
  const typeSelectId = `${baseId}-type`;
  const modalitySelectId = `${baseId}-modality`;
  const roomSelectId = `${baseId}-room`;
  const valueInputId = `${baseId}-session-value`;

  return (
    <section className="space-y-3 border-t border-border pt-4">
      <SectionLabel>Detalhes</SectionLabel>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Duração" htmlFor={durationSelectId}>
          <select
            id={durationSelectId}
            value={form.duration}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                duration: event.target.value,
              }))
            }
            className={fieldClass}
            disabled={disabled}
          >
            {[30, 45, 50, 60, 90, 120].map((value) => (
              <option key={value} value={value}>
                {value} min
              </option>
            ))}
          </select>
        </Field>
        <Field label="Tipo" htmlFor={typeSelectId}>
          <select
            id={typeSelectId}
            value={form.appointmentType}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                appointmentType: event.target.value as AppointmentType,
              }))
            }
            className={fieldClass}
            disabled={disabled}
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
        <Field label="Modalidade" htmlFor={modalitySelectId}>
          <select
            id={modalitySelectId}
            value={form.modality}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                modality: event.target.value as AppointmentModality,
                room: event.target.value === "online" ? "" : current.room,
              }))
            }
            className={fieldClass}
            disabled={disabled}
          >
            <option value="in_person">Presencial</option>
            <option value="online">Online</option>
            <option value="hybrid">Híbrida</option>
          </select>
        </Field>
        <Field label="Sala" htmlFor={roomSelectId}>
          <select
            id={roomSelectId}
            value={form.room}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                room: event.target.value,
              }))
            }
            className={fieldClass}
            disabled={disabled || form.modality === "online"}
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
      <Field label="Valor (R$)" htmlFor={valueInputId}>
        <input
          id={valueInputId}
          inputMode="decimal"
          value={form.sessionValue}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              sessionValue: event.target.value.replace(",", "."),
            }))
          }
          className={fieldClass}
          disabled={disabled}
        />
      </Field>
    </section>
  );
}
