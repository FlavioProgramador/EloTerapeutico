import { getPublicErrorMessage } from "@/lib/errors/public-error";

import type {
  ChannelConnectionStatus,
  CommunicationChannel,
  CommunicationStatus,
} from "./types";

export const communicationStatusLabel: Record<CommunicationStatus, string> = {
  draft: "Rascunho",
  scheduled: "Agendada",
  queued: "Na fila",
  processing: "Processando",
  sent: "Enviada",
  delivered: "Entregue",
  read: "Lida",
  responded: "Respondida",
  failed: "Falhou",
  canceled: "Cancelada",
  expired: "Expirada",
};

export const communicationChannelLabel: Record<CommunicationChannel, string> = {
  in_app: "Interna",
  email: "E-mail",
  whatsapp_manual: "WhatsApp manual",
  whatsapp: "WhatsApp Business",
  sms: "SMS",
};

export const communicationConnectionStatusLabel: Record<
  ChannelConnectionStatus,
  string
> = {
  not_configured: "Não configurado",
  incomplete: "Configuração incompleta",
  validating: "Validando",
  configured: "Configurado",
  error: "Com erro",
  disabled: "Desativado",
  unavailable: "Indisponível temporariamente",
};

export function getCommunicationApiErrorMessage(
  error: unknown,
  fallback = "Não foi possível concluir a comunicação.",
): string {
  return getPublicErrorMessage(error, fallback);
}

export function canCancelCommunication(status: CommunicationStatus): boolean {
  return ["draft", "scheduled", "queued", "failed"].includes(status);
}

export function canRetryCommunication(status: CommunicationStatus): boolean {
  return status === "failed";
}

export function isManualWhatsAppReady(
  channel: CommunicationChannel,
  status: CommunicationStatus,
  manualUrl?: string,
): boolean {
  return (
    channel === "whatsapp_manual" && status === "draft" && Boolean(manualUrl)
  );
}

export function canActivateCommunicationChannel(
  status: ChannelConnectionStatus,
): boolean {
  return status === "configured";
}
