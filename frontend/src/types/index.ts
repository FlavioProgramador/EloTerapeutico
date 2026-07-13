/**
 * Tipos compartilhados do domínio do Elo Terapêutico.
 * Espelham os serializadores do backend (DRF) para garantir tipagem fim-a-fim.
 */

// ─── Autenticação ──────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "therapist" | "secretary" | "admin";
  specialty?: string;
  crp?: string;
  phone?: string;
  default_session_value?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user?: User;
}

// ─── Pacientes ─────────────────────────────────────────────────────────────────

export type PatientStatus =
  | "active"
  | "evaluation"
  | "waiting_return"
  | "discharged"
  | "inactive"
  | "archived"
  | "on_hold";

export type PaymentMethod = "pix" | "credit_card" | "cash" | "insurance" | "boleto";
export type FinancialPaymentMethod =
  | "pix"
  | "credit_card"
  | "debit_card"
  | "cash"
  | "bank_transfer"
  | "boleto"
  | "uninformed"
  | "payment_link"
  | "other";

export interface Patient {
  id: number;
  full_name: string;
  social_name?: string;
  email?: string;
  phone?: string;
  whatsapp?: string;
  birth_date?: string;
  cpf?: string;
  formatted_cpf?: string;
  masked_cpf?: string;
  rg?: string;
  gender?: "M" | "F" | "O" | "N";
  marital_status?: string;
  address?: string | Record<string, unknown>;
  status: PatientStatus;
  status_display?: string;
  attendance_type?: string;
  modality?: string;
  payer_type?: string;
  insurance_name?: string;
  session_value?: string;
  planned_frequency?: string;
  payment_method?: PaymentMethod;
  tags?: string[];
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  referral_source?: string;
  guardian_name?: string;
  guardian_cpf?: string;
  guardian_phone?: string;
  guardian_email?: string;
  guardian_relationship?: string;
  consent_terms_accepted?: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  therapist?: number;
  therapist_name?: string;
  age?: number;
}

export interface CreatePatientPayload {
  full_name: string;
  social_name?: string;
  email?: string;
  phone?: string;
  whatsapp?: string;
  birth_date?: string;
  cpf?: string;
  rg?: string;
  gender?: "M" | "F" | "O" | "N";
  marital_status?: string;
  address?: string | Record<string, unknown>;
  status?: PatientStatus;
  attendance_type?: string;
  modality?: string;
  payer_type?: string;
  insurance_name?: string;
  session_value?: string;
  planned_frequency?: string;
  payment_method?: PaymentMethod;
  tags?: string[];
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  referral_source?: string;
  guardian_name?: string;
  guardian_cpf?: string;
  guardian_phone?: string;
  guardian_email?: string;
  guardian_relationship?: string;
  consent_terms_accepted?: boolean;
  notes?: string;
  therapist?: number;
}

// ─── Agenda ────────────────────────────────────────────────────────────────────

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "missed";

export interface Appointment {
  id: number;
  patient: number;
  patient_name?: string;
  therapist?: number;
  therapist_name?: string;
  date: string;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  status_display?: string;
  notes?: string;
  google_event_id?: string;
  created_at: string;
  updated_at: string;
  is_recurring?: boolean;
  duration_display?: string;
  session_value?: string;
  cancellation_reason?: string;
  recurrence_rule?: string | null;
  evolution_id?: number | null;
  evolution_status?: string | null;
}

export interface CreateAppointmentPayload {
  patient: number;
  date?: string;
  start_time: string;
  end_time: string;
  status?: AppointmentStatus;
  notes?: string;
  session_value?: string;
  is_recurring?: boolean;
  recurrence_rule?: string | null;
}

// ─── Prontuários ───────────────────────────────────────────────────────────────

export interface Anamnesis {
  id?: number;
  patient_id?: number;
  chief_complaint: string;
  history: string;
  medications: string;
  family_history: string;
  observations: string;
  created_at?: string;
  updated_at?: string;
  created_by?: {
    id: number;
    full_name: string;
    email: string;
  };
}

export interface EvolutionListItem {
  id: number;
  patient: number;
  session_date: string;
  cid10: string;
  is_locked: boolean;
  locked_at: string | null;
  is_editable: boolean;
  addenda_count: number;
  created_by: number;
  created_by_name: string;
  created_at: string;
}

export interface Addendum {
  id: number;
  evolution: number;
  reason: string;
  content: string;
  created_by: {
    id: number;
    full_name: string;
    email: string;
  };
  created_at: string;
}

export interface EvolutionDetail extends Omit<EvolutionListItem, "created_by"> {
  content: string;
  addenda: Addendum[];
  created_by: {
    id: number;
    full_name: string;
    email: string;
  };
  updated_at: string;
}

export interface CreateEvolutionPayload {
  patient: number;
  appointment?: number | null;
  content: string;
  cid10?: string;
  session_date: string;
}

export interface CreateAddendumPayload {
  reason: string;
  content: string;
}

// ─── Financeiro ────────────────────────────────────────────────────────────────

export type TransactionType = "income" | "expense";
export type TransactionStatus = "pending" | "paid" | "overdue" | "cancelled" | "refunded";

export interface FinancialTransaction {
  id: number;
  patient?: number;
  patient_name?: string;
  appointment?: number;
  description: string;
  amount: string;
  type: TransactionType;
  category: "session" | "subscription" | "material" | "refund" | "other";
  category_display?: string;
  status: TransactionStatus;
  due_date: string;
  payment_date?: string;
  payment_method?: FinancialPaymentMethod;
  is_overdue?: boolean;
  notes?: string;
  payment_link?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTransactionPayload {
  patient?: number;
  appointment?: number;
  description: string;
  amount: string | number;
  type: TransactionType;
  category: "session" | "subscription" | "material" | "refund" | "other";
  status?: TransactionStatus;
  due_date: string;
  payment_date?: string;
  payment_method?: FinancialPaymentMethod;
  notes?: string;
  payment_link?: string;
}

// ─── Respostas paginadas ────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next?: string | null;
  previous?: string | null;
  results: T[];
}

// ─── Erros de API ──────────────────────────────────────────────────────────────

export interface ApiError {
  message: string;
  status?: number;
  details?: Record<string, string[]>;
}
