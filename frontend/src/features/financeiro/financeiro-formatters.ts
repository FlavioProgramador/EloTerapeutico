export function formatCurrency(value?: string | number, hidden = false) {
  if (hidden) return "R$ ••••••";
  const parsed = typeof value === "number" ? value : Number(value ?? 0);
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number.isFinite(parsed) ? parsed : 0);
}

export function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(
    new Date(`${value.slice(0, 10)}T12:00:00Z`),
  );
}

export function currentMonthRange() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const iso = (date: Date) => date.toISOString().slice(0, 10);
  return { startDate: iso(start), endDate: iso(end) };
}

export const TRANSACTION_STATUS_LABELS: Record<string, string> = {
  pending: "Pendente",
  partial: "Parcialmente pago",
  paid: "Pago",
  overdue: "Vencido",
  cancelled: "Cancelado",
  refunded: "Estornado",
};
