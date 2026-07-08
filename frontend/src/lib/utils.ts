import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * cn – Mescla classes CSS condicionalmente e resolve conflitos Tailwind.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formata um valor monetário em BRL.
 */
export function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "R$ 0,00";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(num);
}

/**
 * Formata uma data ISO em formato brasileiro.
 */
export function formatDate(
  date: string | Date,
  options: Intl.DateTimeFormatOptions = {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }
): string {
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", options).format(d);
}

/**
 * Formata hora no padrão HH:MM.
 */
export function formatTime(timeStr: string): string {
  if (!timeStr) return "—";
  return timeStr.substring(0, 5);
}

export function extractApiError(error: unknown): string {
  const err = error as {
    response?: {
      data?: Record<string, unknown> | string | null;
    };
  };
  const details = err?.response?.data;

  if (details) {
    if (typeof details === "string") return details;

    const dataObj = details as Record<string, unknown>;
    if (typeof dataObj.detail === "string") return dataObj.detail;

    const errObj = dataObj.error as Record<string, unknown> | undefined;
    if (errObj && typeof errObj.message === "string") return errObj.message;

    const nonFieldErrors = dataObj.non_field_errors;
    if (Array.isArray(nonFieldErrors) && typeof nonFieldErrors[0] === "string") {
      return nonFieldErrors[0];
    }

    const firstKey = Object.keys(dataObj)[0];
    if (firstKey) {
      const fieldErrors = dataObj[firstKey];
      if (Array.isArray(fieldErrors) && typeof fieldErrors[0] === "string") {
        return `${firstKey}: ${fieldErrors[0]}`;
      }
    }
  }

  return "Ocorreu um erro inesperado. Tente novamente.";
}

/**
 * Trunca texto longo com reticências.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength).trimEnd() + "…";
}

/**
 * Gera iniciais a partir de um nome completo.
 */
export function getInitials(name: string): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
