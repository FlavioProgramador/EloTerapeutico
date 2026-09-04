import { useId } from "react";
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
  disabled?: boolean;
}

export function AppointmentDetailsSection({
  form,
  setForm,
  rooms,
  disabled,
}: AppointmentDetailsSectionProps) {
  const baseId = useId();
  const durationId = `${baseId}-duration`;
  const appointmentTypeId = `${baseId}-type`;
  const modalityId = `${baseId}-modality`;
  const roomId = `${baseId}-room`;
  const sessionValueId = `${baseId}-session-value`;

  return (
    <section className="space-y-3 border-t border-border pt-4">
      <SectionLabel>Detalhes</SectionLabel>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Duração" htmlFor={durationId}>
          <select
            id={durationId}
            value={form.duration}
            disabled={disabled}
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
        <Field label="Tipo" htmlFor={appointmentTypeId}>
          <select
            id={appointmentTypeId}
            value={form.appointmentType}
            disabled={disabled}
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
        <Field label="Modalidade" htmlFor={modalityId}>
          <select
            id={modalityId}
            value={form.modality}
            disabled={disabled}
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
        <Field label="Sala" htmlFor={roomId}>
          <select
            id={roomId}
            value={form.room}
            disabled={disabled || form.modality === "online"}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                room: event.target.value,
              }))
            }
            className={fieldClass}
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
      <Field label="Valor (R$)" htmlFor={sessionValueId}>
        <input
          id={sessionValueId}
          inputMode="decimal"
          value={form.sessionValue}
          disabled={disabled}
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
  );
}
