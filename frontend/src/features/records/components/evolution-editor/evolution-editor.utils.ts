import type { KeyboardEvent as ReactKeyboardEvent } from "react";

import type { EvolutionAppointmentOption } from "../../evolution-modal.types";
import type {
  EvolutionEditorFormState,
  EvolutionWithModalData,
} from "./evolution-editor.types";

export const evolutionFieldClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15 disabled:cursor-not-allowed disabled:opacity-60";

export function createEvolutionEditorForm(
  evolution?: EvolutionWithModalData | null,
): EvolutionEditorFormState {
  return {
    appointment: evolution?.appointment ? String(evolution.appointment) : "",
    sessionDate: evolution?.session_date || toDateInput(new Date()),
    content: evolution?.content || evolution?.therapist_observations || "",
    confidential: Boolean(evolution?.is_confidential),
    dateOverrideConfirmed: false,
  };
}

export function toDateInput(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatEvolutionDate(value: string) {
  return new Date(value).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatAppointmentOption(item: EvolutionAppointmentOption) {
  const start = new Date(item.start_time);
  return `${start.toLocaleDateString("pt-BR")} às ${start.toLocaleTimeString(
    "pt-BR",
    { hour: "2-digit", minute: "2-digit" },
  )} — ${item.type_display} · ${item.therapist_name} · ${item.status_display}`;
}

export function getEvolutionApiErrors(
  error: unknown,
): Record<string, string> {
  if (!error || typeof error !== "object" || !("response" in error)) {
    return {
      form: "Falha de conexão. Verifique sua internet e tente novamente.",
    };
  }

  const response = (
    error as { response?: { data?: unknown; status?: number } }
  ).response;
  const data = response?.data;
  const status = response?.status;

  if (status === 401) return { form: "Sua sessão expirou. Entre novamente." };
  if (status === 403)
    return { form: "Você não possui permissão para esta ação." };
  if (status === 409)
    return {
      form: "O registro foi alterado por outro usuário. Recarregue a página.",
    };
  if (!data || typeof data !== "object") {
    return { form: "O servidor não conseguiu concluir a operação." };
  }

  const result: Record<string, string> = {};
  Object.entries(data as Record<string, unknown>).forEach(([key, value]) => {
    if (typeof value === "string") result[normalizeEvolutionErrorKey(key)] = value;
    else if (Array.isArray(value) && typeof value[0] === "string") {
      result[normalizeEvolutionErrorKey(key)] = value[0];
    }
  });
  if (!Object.keys(result).length) {
    result.form = "Revise os dados e tente novamente.";
  }
  return result;
}

export function getEvolutionApiMessage(error: unknown, fallback: string) {
  const messages = getEvolutionApiErrors(error);
  return messages.form || Object.values(messages)[0] || fallback;
}

function normalizeEvolutionErrorKey(key: string) {
  if (key === "session_date") return "sessionDate";
  if (key === "non_field_errors" || key === "detail") return "form";
  return key;
}

export function handleEditorShortcut(
  event: ReactKeyboardEvent,
  action: () => void,
) {
  if (event.key === "Enter") action();
}
