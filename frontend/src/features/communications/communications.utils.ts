import type { ChannelConnectionStatus, CommunicationChannel, CommunicationStatus } from "./types";

export const communicationStatusLabel: Record<CommunicationStatus, string> = { draft: "Rascunho", scheduled: "Agendada", queued: "Na fila", processing: "Processando", sent: "Enviada", delivered: "Entregue", read: "Lida", responded: "Respondida", failed: "Falhou", canceled: "Cancelada", expired: "Expirada" };
export const communicationChannelLabel: Record<CommunicationChannel, string> = { in_app: "Interna", email: "E-mail", whatsapp_manual: "WhatsApp manual", whatsapp: "WhatsApp Business", sms: "SMS" };
export const communicationConnectionStatusLabel: Record<ChannelConnectionStatus, string> = { not_configured: "Não configurado", incomplete: "Configuração incompleta", validating: "Validando", configured: "Configurado", error: "Com erro", disabled: "Desativado", unavailable: "Indisponível temporariamente" };

const fieldLabels: Record<string, string> = {
  patient_id: "Paciente",
  body: "Mensagem",
  template_id: "Template",
  scheduled_at: "Agendamento",
  channel: "Canal",
  category: "Categoria",
  recipient_type: "Destinatário",
  non_field_errors: "Validação",
};

function normalizeApiMessage(message: string): string {
  const trimmed = message.trim();
  for (const [field, label] of Object.entries(fieldLabels)) {
    const prefix = `${field}:`;
    if (trimmed.startsWith(prefix)) {
      return `${label}: ${trimmed.slice(prefix.length).trim()}`;
    }
  }
  return trimmed;
}

function firstErrorMessage(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return normalizeApiMessage(value);
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstErrorMessage(item);
      if (message) return message;
    }
    return null;
  }
  if (!value || typeof value !== "object") return null;

  const record = value as Record<string, unknown>;
  for (const preferredKey of ["message", "detail", "non_field_errors"]) {
    const message = firstErrorMessage(record[preferredKey]);
    if (message) return message;
  }
  for (const [key, item] of Object.entries(record)) {
    if (["code", "message", "detail", "non_field_errors"].includes(key)) continue;
    const message = firstErrorMessage(item);
    if (message) return `${fieldLabels[key] ?? key}: ${message}`;
  }
  return null;
}

export function getCommunicationApiErrorMessage(
  error: unknown,
  fallback = "Não foi possível criar a comunicação.",
): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data;
  if (!data || typeof data !== "object") return fallback;

  const payload = data as Record<string, unknown>;
  const apiError = payload.error;
  if (apiError && typeof apiError === "object") {
    const structuredError = apiError as Record<string, unknown>;
    const message = firstErrorMessage(structuredError.message);
    if (message) return message;
    const details = firstErrorMessage(structuredError.details);
    if (details) return details;
  }

  return firstErrorMessage(data) ?? fallback;
}

export function canCancelCommunication(status: CommunicationStatus): boolean { return ["draft", "scheduled", "queued", "failed"].includes(status); }
export function canRetryCommunication(status: CommunicationStatus): boolean { return status === "failed"; }
export function isManualWhatsAppReady(channel: CommunicationChannel, status: CommunicationStatus, manualUrl?: string): boolean { return channel === "whatsapp_manual" && status === "draft" && Boolean(manualUrl); }
export function canActivateCommunicationChannel(status: ChannelConnectionStatus): boolean { return status === "configured"; }
