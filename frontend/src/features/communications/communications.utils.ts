import type { CommunicationChannel, CommunicationStatus } from "./types";
export const communicationStatusLabel: Record<CommunicationStatus, string> = { draft: "Rascunho", scheduled: "Agendada", queued: "Na fila", processing: "Processando", sent: "Enviada", delivered: "Entregue", read: "Lida", responded: "Respondida", failed: "Falhou", canceled: "Cancelada", expired: "Expirada" };
export const communicationChannelLabel: Record<CommunicationChannel, string> = { in_app: "Interna", email: "E-mail", whatsapp_manual: "WhatsApp manual", whatsapp: "WhatsApp Business", sms: "SMS" };
export function canCancelCommunication(status: CommunicationStatus): boolean { return ["draft", "scheduled", "queued", "failed"].includes(status); }
export function canRetryCommunication(status: CommunicationStatus): boolean { return status === "failed"; }
export function isManualWhatsAppReady(channel: CommunicationChannel, status: CommunicationStatus, manualUrl?: string): boolean { return channel === "whatsapp_manual" && status === "draft" && Boolean(manualUrl); }
