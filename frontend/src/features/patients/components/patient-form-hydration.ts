import type { PatientFormData } from "../schemas/patient.schemas";
import type { PatientFormRecord } from "../types/patient-form.types";
import { EMPTY_PATIENT_FORM } from "./patient-form-defaults";
import {
  decimalToCurrency,
  formatCep,
  formatCpf,
  formatPhone,
} from "./patient-form-formatters";

export function recordToPatientForm(
  record: PatientFormRecord,
): PatientFormData {
  const address =
    record.address && typeof record.address === "object" ? record.address : {};
  const legacyAddress =
    typeof record.address === "string" ? record.address : address.street ?? "";
  return {
    ...EMPTY_PATIENT_FORM,
    full_name: record.full_name ?? "",
    social_name: record.social_name ?? "",
    email: record.email ?? "",
    phone: record.phone ? formatPhone(record.phone) : "",
    whatsapp: record.whatsapp ? formatPhone(record.whatsapp) : "",
    birth_date: record.birth_date ?? "",
    treatment_start_date: record.treatment_start_date ?? "",
    cpf: record.cpf ? formatCpf(record.cpf) : "",
    rg: record.rg ?? "",
    profession: record.profession ?? "",
    social_network: record.social_network ?? "",
    gender: record.gender ?? "N",
    marital_status: record.marital_status ?? "",
    status: record.status,
    attendance_type:
      (record.attendance_type as PatientFormData["attendance_type"]) ??
      "individual",
    modality:
      (record.modality as PatientFormData["modality"]) ?? "in_person",
    payer_type:
      (record.payer_type as PatientFormData["payer_type"]) ?? "private",
    insurance_name: record.insurance_name ?? "",
    session_value: decimalToCurrency(record.session_value),
    planned_frequency: record.planned_frequency ?? "",
    reminders_enabled: record.reminders_enabled ?? true,
    reminder_recipient: record.reminder_recipient ?? "patient",
    therapist: record.therapist ? String(record.therapist) : "",
    tags: record.tags?.join(", ") ?? "",
    referral_source: record.referral_source ?? "",
    address: legacyAddress,
    address_zip_code: address.zip_code ? formatCep(address.zip_code) : "",
    address_street: address.street ?? "",
    address_number: address.number ?? "",
    address_complement: address.complement ?? "",
    address_neighborhood: address.neighborhood ?? "",
    address_city: address.city ?? "",
    address_state: address.state ?? "",
    emergency_contact_name: record.emergency_contact_name ?? "",
    emergency_contact_relationship: record.emergency_contact_relationship ?? "",
    emergency_contact_phone: record.emergency_contact_phone
      ? formatPhone(record.emergency_contact_phone)
      : "",
    guardian_name: record.guardian_name ?? "",
    guardian_cpf: record.guardian_cpf ? formatCpf(record.guardian_cpf) : "",
    guardian_phone: record.guardian_phone
      ? formatPhone(record.guardian_phone)
      : "",
    guardian_email: record.guardian_email ?? "",
    guardian_relationship: record.guardian_relationship ?? "",
    financial_responsible_name: record.financial_responsible_name ?? "",
    financial_responsible_cpf: record.financial_responsible_cpf
      ? formatCpf(record.financial_responsible_cpf)
      : "",
    financial_responsible_phone: record.financial_responsible_phone
      ? formatPhone(record.financial_responsible_phone)
      : "",
    financial_responsible_email: record.financial_responsible_email ?? "",
    financial_responsible_marital_status:
      record.financial_responsible_marital_status ?? "",
    financial_responsible_naturality:
      record.financial_responsible_naturality ?? "",
    financial_responsible_occupation:
      record.financial_responsible_occupation ?? "",
    financial_responsible_relationship:
      record.financial_responsible_relationship ?? "",
    consent_terms_accepted: record.consent_terms_accepted ?? false,
    notes: record.notes ?? "",
  };
}
