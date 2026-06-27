/**
 * Badge – Componente de rótulo/estado tipado.
 * Cobre todos os estados de domínio do Elo Terapêutico.
 * Design discreto, sem exageros visuais.
 */

import React from "react";

type BadgeVariant =
  | "default"
  | "primary"
  | "success"
  | "warning"
  | "destructive"
  | "outline"
  | "muted";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default:
    "bg-primary/10 text-primary border-primary/20",
  primary:
    "bg-primary text-primary-foreground border-transparent",
  success:
    "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800",
  warning:
    "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800",
  destructive:
    "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800",
  outline:
    "bg-transparent text-foreground border-border",
  muted:
    "bg-muted text-muted-foreground border-transparent",
};

export function Badge({ variant = "default", children, className = "" }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1
        rounded-md border
        px-2 py-0.5
        text-xs font-medium
        leading-none
        transition-colors
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}

// ─── Helpers para estados de domínio ──────────────────────────────────────────

/**
 * Retorna a variante correta para status de paciente.
 */
export function getPatientStatusVariant(
  status: string
): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    active: "success",
    inactive: "muted",
    on_hold: "warning",
  };
  return map[status] ?? "outline";
}

/**
 * Retorna a variante correta para status de agendamento.
 */
export function getAppointmentStatusVariant(
  status: string
): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    scheduled: "default",
    confirmed: "primary",
    completed: "success",
    cancelled: "muted",
    missed: "destructive",
  };
  return map[status] ?? "outline";
}

/**
 * Retorna a variante correta para status financeiro.
 */
export function getTransactionStatusVariant(
  status: string
): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    pending: "warning",
    paid: "success",
    overdue: "destructive",
    cancelled: "muted",
    refunded: "outline",
  };
  return map[status] ?? "outline";
}
