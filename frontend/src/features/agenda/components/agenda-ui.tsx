"use client";

import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgendaPagination, AppointmentStatus } from "../types";

export const fieldClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-60";

export function Toolbar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card p-3">
      {children}
    </div>
  );
}

export function SearchInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <div className="relative min-w-[220px] flex-1">
      <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className={cn(
          "h-9 w-full rounded-md border border-border bg-background pl-9 text-sm outline-none transition focus:border-primary",
          value ? "pr-9" : "pr-3",
        )}
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          className="absolute right-2 top-1.5 flex items-center justify-center rounded-md p-1 text-muted-foreground transition hover:bg-secondary hover:text-foreground"
          aria-label="Limpar busca"
        >
          <X className="size-3.5" />
        </button>
      )}
    </div>
  );
}

export function FilterSelect({
  value,
  onChange,
  label,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label>
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 rounded-md border border-border bg-background px-3 text-xs font-medium"
      >
        {children}
      </select>
    </label>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs font-semibold text-foreground">{label}</span>
      {children}
      {hint && (
        <span className="block text-[11px] text-muted-foreground">{hint}</span>
      )}
    </label>
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
      {children}
    </p>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  description?: string;
}) {
  return (
    <label className="flex cursor-pointer items-start justify-between gap-4 rounded-lg border border-border bg-secondary/10 p-3">
      <span>
        <strong className="block text-sm font-medium">{label}</strong>
        {description && (
          <span className="mt-0.5 block text-xs text-muted-foreground">
            {description}
          </span>
        )}
      </span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="mt-1"
      />
    </label>
  );
}

export function TableShell({
  loading,
  empty,
  emptyText,
  children,
}: {
  loading: boolean;
  empty: boolean;
  emptyText: string;
  children: React.ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border bg-card">
      {loading ? (
        <div className="animate-pulse space-y-2 p-4">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="h-14 rounded-lg bg-secondary" />
          ))}
        </div>
      ) : empty ? (
        <div className="grid min-h-48 place-items-center p-8 text-sm text-muted-foreground">
          {emptyText}
        </div>
      ) : (
        children
      )}
    </div>
  );
}

const statusLabels: Record<string, string> = {
  scheduled: "Agendado",
  confirmed: "Confirmado",
  completed: "Realizado",
  missed: "Falta",
  cancelled: "Cancelado",
  rescheduled: "Remarcado",
  active: "Ativo",
  paused: "Pausado",
  ended: "Encerrado",
  expired: "Expirado",
  pending: "Pendente",
  available: "Disponível",
  in_progress: "Em andamento",
  finished: "Finalizada",
};

export function StatusBadge({
  status,
}: {
  status: string | AppointmentStatus;
}) {
  return (
    <span
      className={cn(
        "inline-flex w-fit items-center rounded-full border px-2 py-1 text-[11px] font-semibold",
        status === "confirmed" || status === "active" || status === "available"
          ? "border-primary/25 bg-primary/10 text-primary"
          : status === "scheduled" || status === "pending"
            ? "border-warning/25 bg-warning/10 text-warning"
            : status === "completed" || status === "finished"
              ? "border-success/25 bg-success/10 text-success"
              : status === "missed" ||
                  status === "cancelled" ||
                  status === "expired"
                ? "border-destructive/25 bg-destructive/10 text-destructive"
                : "border-border bg-secondary text-muted-foreground",
      )}
    >
      {statusLabels[status] || status}
    </span>
  );
}

export function PaginationSummary({ page }: { page?: AgendaPagination }) {
  if (!page) return null;
  return (
    <p className="text-xs text-muted-foreground">
      Mostrando {page.count} registro{page.count === 1 ? "" : "s"} · Página{" "}
      {page.current_page} de {Math.max(page.total_pages, 1)}
    </p>
  );
}

export function formatDate(value: string | Date) {
  return new Date(value).toLocaleDateString("pt-BR");
}

export function formatDateTime(value: string | Date) {
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
