/**
 * Constantes globais da aplicação.
 * Centraliza strings reutilizadas para evitar magic strings espalhadas pelo código.
 */

// ─── Query Keys (TanStack Query) ─────────────────────────────────────────────
// Usa objetos para garantir tipagem e facilitar invalidação por prefixo.

export const QUERY_KEYS = {
  // Auth
  me: ["auth", "me"] as const,

  // Patients
  patients: ["patients"] as const,
  patient: (id: number) => ["patients", id] as const,

  // Agenda
  appointments: ["appointments"] as const,
  appointmentsByDate: (date: string) => ["appointments", "date", date] as const,
  appointment: (id: number) => ["appointments", id] as const,

  // Records
  records: ["records"] as const,
  recordsByPatient: (patientId: number) =>
    ["records", "patient", patientId] as const,
  record: (id: number) => ["records", id] as const,

  // Financeiro
  transactions: ["transactions"] as const,
  transactionsSummary: ["transactions", "summary"] as const,
  transaction: (id: number) => ["transactions", id] as const,
} as const;

// ─── Status Labels ────────────────────────────────────────────────────────────

export const PATIENT_STATUS_LABELS: Record<string, string> = {
  active: "Ativo",
  inactive: "Inativo",
  on_hold: "Em Espera",
};

export const APPOINTMENT_STATUS_LABELS: Record<string, string> = {
  scheduled: "Agendado",
  confirmed: "Confirmado",
  completed: "Realizado",
  cancelled: "Cancelado",
  missed: "Faltou",
};

export const TRANSACTION_STATUS_LABELS: Record<string, string> = {
  pending: "Pendente",
  paid: "Pago",
  overdue: "Vencido",
  cancelled: "Cancelado",
};

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  pix: "PIX",
  credit_card: "Cartão de Crédito",
  cash: "Dinheiro",
  insurance: "Convênio",
  boleto: "Boleto",
};

// ─── Rotas ────────────────────────────────────────────────────────────────────

export const ROUTES = {
  home: "/",
  login: "/login",
  register: "/register",
  dashboard: "/dashboard",
  patients: "/dashboard/patients",
  agenda: "/dashboard/agenda",
  records: "/dashboard/records",
  financeiro: "/dashboard/financeiro",
} as const;

// ─── Roles ────────────────────────────────────────────────────────────────────

export const ROLE_LABELS: Record<string, string> = {
  therapist: "Terapeuta",
  secretary: "Secretária",
  admin: "Administrador",
};
