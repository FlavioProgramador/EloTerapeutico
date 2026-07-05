/**
 * Constantes globais da aplicação.
 * Centraliza strings reutilizadas para evitar magic strings espalhadas pelo código.
 */

export const QUERY_KEYS = {
  me: ["auth", "me"] as const,
  patients: ["patients"] as const,
  patient: (id: number | undefined) => ["patients", id] as const,
  appointments: ["appointments"] as const,
  appointmentsByDate: (date: string) => ["appointments", "date", date] as const,
  appointment: (id: number) => ["appointments", id] as const,
  records: ["records"] as const,
  recordsByPatient: (patientId: number) =>
    ["records", "patient", patientId] as const,
  record: (id: number) => ["records", id] as const,
  anamnesis: (patientId: number) => ["records", "anamnesis", patientId] as const,
  transactions: ["transactions"] as const,
  transactionsSummary: ["transactions", "summary"] as const,
  transaction: (id: number) => ["transactions", id] as const,
  documentTemplates: ["documents", "templates"] as const,
  generatedDocuments: ["documents", "generated"] as const,
  documentLibrary: ["documents", "library"] as const,
  evolutionTemplates: ["documents", "evolution-templates"] as const,
} as const;

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
  refunded: "Estornado",
};

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  pix: "PIX",
  debit_card: "Cartao de Debito",
  credit_card: "Cartão de Crédito",
  cash: "Dinheiro",
  bank_transfer: "Transferencia Bancaria",
  other: "Outro",
  insurance: "Convênio",
  boleto: "Boleto",
};

export const ROUTES = {
  home: "/",
  login: "/login",
  register: "/register",
  dashboard: "/dashboard",
  patients: "/dashboard/patients",
  agenda: "/dashboard/agenda",
  records: "/dashboard/records",
  financeiro: "/dashboard/financeiro",
  documents: "/dashboard/documentos",
} as const;

export const ROLE_LABELS: Record<string, string> = {
  therapist: "Terapeuta",
  secretary: "Secretária",
  admin: "Administrador",
};
