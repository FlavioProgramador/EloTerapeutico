import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import { getPublicErrorMessage } from "./errors/public-error.ts";

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
  },
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

/**
 * Compatibilidade para módulos antigos. Toda mensagem passa pela política
 * pública central e nunca retorna o corpo bruto da API.
 */
export function extractApiError(
  error: unknown,
  fallback = "Ocorreu um erro inesperado. Tente novamente.",
): string {
  return getPublicErrorMessage(error, fallback);
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
