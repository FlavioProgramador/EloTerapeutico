import type { FinancialPaymentMethod, FinancialTransaction, TransactionStatus } from "@/types";

export type FinanceTab = "receive" | "pay" | "subscriptions";
export type FinanceModal = "income" | "expense" | "charge" | "subscription" | "batch" | null;
export type FinanceFormState = {
  patient: string;
  appointment: string;
  amount: string;
  dueDate: string;
  paymentMethod: FinancialPaymentMethod;
  status: "pending" | "paid";
  description: string;
  frequency: "weekly" | "biweekly" | "monthly";
  weekday: string;
  time: string;
};
export type UnbilledAppointment = {
  id: number;
  patient_id: number;
  patient_name: string;
  start_time: string;
  end_time: string;
  session_value: string;
};

export const MONTHS = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
export const PAYMENT_METHODS: Array<{ value: FinancialPaymentMethod; label: string }> = [
  { value: "pix", label: "PIX" },
  { value: "credit_card", label: "Cartão de crédito" },
  { value: "debit_card", label: "Cartão de débito" },
  { value: "cash", label: "Dinheiro" },
  { value: "bank_transfer", label: "Transferência bancária" },
  { value: "other", label: "Outro" },
];
export const STATUS_LABEL: Record<TransactionStatus, string> = {
  pending: "Pendente",
  paid: "Pago",
  overdue: "Vencido",
  cancelled: "Cancelado",
  refunded: "Estornado",
};

export function isoToday() {
  return new Date().toISOString().slice(0, 10);
}
export function defaultFinanceForm(): FinanceFormState {
  return { patient: "", appointment: "", amount: "", dueDate: isoToday(), paymentMethod: "pix", status: "pending", description: "", frequency: "weekly", weekday: "1", time: "09:00" };
}
export function parseMoney(value?: string | number) {
  if (typeof value === "number") return value;
  const raw = String(value ?? 0).trim();
  if (!raw) return 0;
  return Number(raw.includes(",") ? raw.replace(/\./g, "").replace(",", ".") : raw) || 0;
}
export function formatMoney(value: number, hidden: boolean) {
  if (hidden) return "R$ •••••";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
}
export function formatDate(value?: string) {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}
export function belongsToMonth(transaction: FinancialTransaction, year: number, month: number) {
  const reference = transaction.due_date || transaction.created_at;
  if (!reference) return false;
  const date = new Date(`${reference.slice(0, 10)}T12:00:00`);
  return date.getFullYear() === year && date.getMonth() + 1 === month;
}
export function transactionStatusClass(status: TransactionStatus) {
  if (status === "paid") return "border-emerald-500/20 bg-emerald-500/10 text-emerald-500";
  if (status === "overdue") return "border-rose-500/20 bg-rose-500/10 text-rose-400";
  if (status === "cancelled" || status === "refunded") return "border-border bg-muted text-muted-foreground";
  return "border-amber-500/20 bg-amber-500/10 text-amber-400";
}
