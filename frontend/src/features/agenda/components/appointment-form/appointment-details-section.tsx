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
  isSubmitting?: boolean;
}

export function AppointmentDetailsSection({
  form,
  setForm,
  rooms,
  isSubmitting = false,
}: AppointmentDetailsSectionProps) {
  const durationId = useId();
  const appointmentTypeId = useId();
  const modalityId = useId();
  const roomId = useId();
  const sessionValueId = useId();

  return (
    <section className="space-y-3 border-t border-border pt-4">
      <SectionLabel>Detalhes</SectionLabel>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Duração" htmlFor={durationId}>
          <select
            id={durationId}
            value={form.duration}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                duration: event.target.value,
              }))
            }
            className={fieldClass}
            disabled={isSubmitting}
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
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                appointmentType: event.target.value as AppointmentType,
              }))
            }
            className={fieldClass}
            disabled={isSubmitting}
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
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                modality: event.target.value as AppointmentModality,
                room: event.target.value === "online" ? "" : current.room,
              }))
            }
            className={fieldClass}
            disabled={isSubmitting}
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
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                room: event.target.value,
              }))
            }
            className={fieldClass}
            disabled={isSubmitting || form.modality === "online"}
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
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              sessionValue: event.target.value.replace(",", "."),
            }))
          }
          className={fieldClass}
          disabled={isSubmitting}
        />
      </Field>
    </section>
  );
}
