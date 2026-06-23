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

export type PatientStatus = "active" | "inactive" | "on_hold";
export type PaymentMethod = "pix" | "credit_card" | "cash" | "insurance" | "boleto";

export interface Patient {
  id: number;
  full_name: string;
  email?: string;
  phone?: string;
  birth_date?: string;
  cpf?: string;
  status: PatientStatus;
  session_value: string;
  payment_method?: PaymentMethod;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  therapist?: number;
  age?: number;
}

export interface CreatePatientPayload {
  full_name: string;
  email?: string;
  phone?: string;
  birth_date?: string;
  cpf?: string;
  status?: PatientStatus;
  session_value: string;
  payment_method?: PaymentMethod;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  notes?: string;
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
  date: string; // ISO 8601
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  status: AppointmentStatus;
  notes?: string;
  google_event_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAppointmentPayload {
  patient: number;
  date: string;
  start_time: string;
  end_time: string;
  status?: AppointmentStatus;
  notes?: string;
}

// ─── Prontuários ───────────────────────────────────────────────────────────────

export interface ClinicalRecord {
  id: number;
  patient: number;
  patient_name?: string;
  appointment?: number;
  content: string;
  is_locked: boolean;
  locked_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateRecordPayload {
  patient: number;
  appointment?: number;
  content: string;
}

// ─── Financeiro ────────────────────────────────────────────────────────────────

export type TransactionType = "income" | "expense";
export type TransactionStatus = "pending" | "paid" | "overdue" | "cancelled";

export interface FinancialTransaction {
  id: number;
  patient?: number;
  patient_name?: string;
  appointment?: number;
  description: string;
  amount: string;
  type: TransactionType;
  status: TransactionStatus;
  due_date: string;
  payment_date?: string;
  payment_method?: PaymentMethod;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTransactionPayload {
  patient?: number;
  appointment?: number;
  description: string;
  amount: string | number;
  type: TransactionType;
  status?: TransactionStatus;
  due_date: string;
  payment_date?: string;
  payment_method?: PaymentMethod;
  notes?: string;
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
