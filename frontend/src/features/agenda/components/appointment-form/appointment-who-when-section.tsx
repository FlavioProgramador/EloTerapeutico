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
}

import { useId } from "react";

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
}: AppointmentWhoWhenSectionProps & { disabled?: boolean }) {
  const baseId = useId();
  const searchPatientId = `${baseId}-search-patient`;
  const patientSelectId = `${baseId}-patient-select`;
  const therapistSelectId = `${baseId}-therapist-select`;
  const dateInputId = `${baseId}-date-input`;
  const timeInputId = `${baseId}-time-input`;
  const freeSlotsSelectId = `${baseId}-free-slots-select`;

  return (
    <section className="space-y-3">
      <SectionLabel>Quem e quando</SectionLabel>
      <Field label="Buscar paciente" htmlFor={searchPatientId}>
        <input
          id={searchPatientId}
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Nome, telefone, e-mail ou CPF..."
          className={fieldClass}
          disabled={disabled}
        />
      </Field>
      <Field label="Paciente *" htmlFor={patientSelectId}>
        <select
          id={patientSelectId}
          value={form.patient}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              patient: event.target.value,
            }))
          }
          className={fieldClass}
          required
          disabled={disabled}
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
        <Field label="Profissional responsável *" htmlFor={therapistSelectId}>
          <select
            id={therapistSelectId}
            value={form.therapist}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                therapist: event.target.value,
              }))
            }
            className={fieldClass}
            required
            disabled={disabled}
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
        <Field label="Data *" htmlFor={dateInputId}>
          <input
            id={dateInputId}
            type="date"
            value={form.date}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                date: event.target.value,
              }))
            }
            className={fieldClass}
            required
            disabled={disabled}
          />
        </Field>
        <Field label="Horário *" htmlFor={timeInputId}>
          <input
            id={timeInputId}
            type="time"
            value={form.time}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                time: event.target.value,
              }))
            }
            className={fieldClass}
            required
            disabled={disabled}
          />
        </Field>
      </div>
      <Field label="Horários livres sugeridos" htmlFor={freeSlotsSelectId}>
        <select
          id={freeSlotsSelectId}
          onChange={(event) => onApplySlot(event.target.value)}
          className={fieldClass}
          defaultValue=""
          disabled={disabled || loadingSlots}
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
