export type PatientFormStatus =
  | "active"
  | "evaluation"
  | "waiting_return"
  | "discharged"
  | "inactive"
  | "archived";

export interface PatientProfessionalOption {
  id: number;
  full_name: string;
  specialty?: string;
  is_primary?: boolean;
}

export interface PatientAddress {
  zip_code?: string;
  street?: string;
  number?: string;
  complement?: string;
  neighborhood?: string;
  city?: string;
  state?: string;
}

export interface PatientFormRecord {
  id: number;
  full_name: string;
  social_name?: string;
  photo?: string | null;
  email?: string;
  phone?: string;
  whatsapp?: string;
  birth_date?: string | null;
  treatment_start_date?: string | null;
  cpf?: string;
  formatted_cpf?: string;
  masked_cpf?: string;
  rg?: string;
  age?: number;
  gender?: "M" | "F" | "O" | "N";
  marital_status?: string;
  profession?: string;
  social_network?: string;
  status: PatientFormStatus;
  status_display?: string;
  attendance_type?: string;
  modality?: string;
  payer_type?: string;
  insurance_name?: string;
  session_value?: string;
  planned_frequency?: string;
  reminders_enabled?: boolean;
  reminder_recipient?: "patient" | "financial_responsible" | "both" | "none";
  therapist?: number;
  therapist_name?: string;
  professionals?: PatientProfessionalOption[];
  address?: PatientAddress | string;
  tags?: string[];
  referral_source?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  guardian_name?: string;
  guardian_cpf?: string;
  guardian_phone?: string;
  guardian_email?: string;
  guardian_relationship?: string;
  financial_responsible_name?: string;
  financial_responsible_cpf?: string;
  financial_responsible_phone?: string;
  financial_responsible_email?: string;
  financial_responsible_marital_status?: string;
  financial_responsible_naturality?: string;
  financial_responsible_occupation?: string;
  financial_responsible_relationship?: string;
  consent_terms_accepted?: boolean;
  notes?: string;
  is_active?: boolean;
  deleted_at?: string | null;
  created_at?: string;
  updated_at?: string;
}

export type PatientFormRequest = Record<
  string,
  | string
  | number
  | boolean
  | string[]
  | PatientAddress
  | File
  | null
  | undefined
>;
