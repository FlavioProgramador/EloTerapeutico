import { useId } from "react";
import type { Patient } from "@/types";
import type { PatientProfessionalOption } from "@/features/patients/types/patient-form.types";
import type { TimeSlot } from "../../types";
import { Field, SectionLabel, fieldClass } from "../agenda-ui";
import type {
  AppointmentFormSetter,
  AppointmentFormState,
} from "./appointment-form.types";

interface AppointmentWhoWhenSectionProps {
  form: AppointmentFormState;
  setForm: AppointmentFormSetter;
  search: string;
  onSearchChange: (value: string) => void;
  patients: Patient[];
  professionals: PatientProfessionalOption[];
  slots: TimeSlot[];
  loadingSlots: boolean;
  showTherapistField: boolean;
  onApplySlot: (value: string) => void;
  disabled?: boolean;
}

export function AppointmentWhoWhenSection({
  form,
  setForm,
  search,
  onSearchChange,
  patients,
  professionals,
  slots,
  loadingSlots,
  showTherapistField,
  onApplySlot,
  disabled,
}: AppointmentWhoWhenSectionProps) {
  const baseId = useId();
  const searchId = `${baseId}-search`;
  const patientId = `${baseId}-patient`;
  const therapistId = `${baseId}-therapist`;
  const dateId = `${baseId}-date`;
  const timeId = `${baseId}-time`;
  const slotsId = `${baseId}-slots`;

  return (
    <section className="space-y-3">
      <SectionLabel>Quem e quando</SectionLabel>
      <Field label="Buscar paciente" htmlFor={searchId}>
        <input
          id={searchId}
          value={search}
          disabled={disabled}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Nome, telefone, e-mail ou CPF..."
          className={fieldClass}
        />
      </Field>
      <Field label="Paciente *" htmlFor={patientId}>
        <select
          id={patientId}
          value={form.patient}
          disabled={disabled}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              patient: event.target.value,
            }))
          }
          className={fieldClass}
          required
        >
          <option value="">Selecione o paciente</option>
          {patients.map((patient) => (
            <option key={patient.id} value={patient.id}>
              {patient.social_name || patient.full_name}
            </option>
          ))}
        </select>
      </Field>
      {showTherapistField && (
        <Field label="Profissional responsável *" htmlFor={therapistId}>
          <select
            id={therapistId}
            value={form.therapist}
            disabled={disabled}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                therapist: event.target.value,
              }))
            }
            className={fieldClass}
            required
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
      <div className="grid grid-cols-2 gap-3">
        <Field label="Data *" htmlFor={dateId}>
          <input
            id={dateId}
            type="date"
            value={form.date}
            disabled={disabled}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                date: event.target.value,
              }))
            }
            className={fieldClass}
            required
          />
        </Field>
        <Field label="Horário *" htmlFor={timeId}>
          <input
            id={timeId}
            type="time"
            value={form.time}
            disabled={disabled}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                time: event.target.value,
              }))
            }
            className={fieldClass}
            required
          />
        </Field>
      </div>
      <Field label="Horários livres sugeridos" htmlFor={slotsId}>
        <select
          id={slotsId}
          disabled={disabled}
          onChange={(event) => onApplySlot(event.target.value)}
          className={fieldClass}
          defaultValue=""
        >
          <option value="">
            {loadingSlots
              ? "Buscando disponibilidade..."
              : slots.length
                ? "Selecione um horário livre"
                : "Nenhum horário livre encontrado"}
          </option>
          {slots.map((slot) => (
            <option key={slot.start_datetime} value={slot.start_datetime}>
              {slot.start}–{slot.end}
            </option>
          ))}
        </select>
      </Field>
    </section>
  );
}
