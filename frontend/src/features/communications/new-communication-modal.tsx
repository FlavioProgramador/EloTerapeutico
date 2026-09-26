"use client";

import { Loader2, Send, X } from "lucide-react";
import { useEffect, useId, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import {
  communicationChannelLabel,
  communicationConnectionStatusLabel,
  getCommunicationApiErrorMessage,
} from "./communications.utils";
import {
  useCommunicationChannels,
  useCommunicationPatients,
  useCommunicationTemplates,
  useCreateCommunication,
} from "./use-communications";
import type { CommunicationChannel, CreateCommunicationPayload } from "./types";

const channelOptions: CommunicationChannel[] = [
  "email",
  "whatsapp_manual",
  "in_app",
  "whatsapp",
  "sms",
];

const focusRingClass =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2";

export function NewCommunicationModal({ onClose }: { onClose: () => void }) {
  const patients = useCommunicationPatients();
  const templates = useCommunicationTemplates();
  const channels = useCommunicationChannels();
  const create = useCreateCommunication();

  const patientSelectId = useId();
  const recipientSelectId = useId();
  const channelSelectId = useId();
  const categorySelectId = useId();
  const templateSelectId = useId();
  const subjectInputId = useId();
  const bodyTextareaId = useId();
  const scheduleCheckboxId = useId();
  const scheduledAtInputId = useId();
  const modalTitleId = useId();
  const modalDescriptionId = useId();

  const [payload, setPayload] = useState<CreateCommunicationPayload>({
    patient_id: null,
    channel: "email",
    category: "patient_message",
    template_id: null,
    subject: "",
    body: "",
    priority: "normal",
    recipient_type: "patient",
    draft: false,
  });
  const [scheduleEnabled, setScheduleEnabled] = useState(false);

  const channelTemplates = (templates.data ?? []).filter(
    (item) =>
      item.channel === payload.channel && item.category === payload.category,
  );
  const selectedTemplate = channelTemplates.find(
    (item) => item.id === payload.template_id,
  );
  const selectedChannelConfig = channels.data?.find(
    (item) => item.channel === payload.channel,
  );
  const selectedChannelReady = Boolean(
    selectedChannelConfig?.is_active &&
    selectedChannelConfig.connection_status === "configured",
  );
  const requiresPatient = payload.channel !== "in_app";

  function handleClose() {
    if (!create.isPending) {
      onClose();
    }
  }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !create.isPending) {
        onClose();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [create.isPending, onClose]);

  function update<K extends keyof CreateCommunicationPayload>(
    key: K,
    value: CreateCommunicationPayload[K],
  ) {
    setPayload((current) => ({ ...current, [key]: value }));
  }

  function changeChannel(channel: CommunicationChannel) {
    setPayload((current) => ({
      ...current,
      channel,
      template_id: null,
      patient_id: channel === "in_app" ? null : current.patient_id,
      category:
        channel === "in_app"
          ? "system_notification"
          : current.category === "system_notification"
            ? "patient_message"
            : current.category,
    }));
  }

  function validateBeforeSubmit(draft: boolean): string | null {
    if (requiresPatient && !payload.patient_id) {
      return "Selecione um paciente para este canal.";
    }
    if (!selectedTemplate && !payload.body?.trim()) {
      return "Escreva o conteúdo da mensagem ou selecione um template.";
    }
    if (scheduleEnabled && !payload.scheduled_at) {
      return "Informe a data e a hora do agendamento.";
    }
    if (!draft && selectedChannelConfig && !selectedChannelReady) {
      const status =
        communicationConnectionStatusLabel[
          selectedChannelConfig.connection_status
        ];
      return `${communicationChannelLabel[payload.channel]} está ${status.toLowerCase()} ou inativo. Configure e ative o canal antes de enviar.`;
    }
    return null;
  }

  async function submit(draft: boolean) {
    const validationError = validateBeforeSubmit(draft);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    try {
      await create.mutateAsync({
        ...payload,
        draft,
        scheduled_at: scheduleEnabled ? payload.scheduled_at : null,
      });
      toast.success(
        draft
          ? "Rascunho salvo."
          : scheduleEnabled
            ? "Comunicação agendada."
            : "Comunicação adicionada à fila.",
      );
      onClose();
    } catch (error) {
      toast.error(
        getCommunicationApiErrorMessage(
          error,
          "Não foi possível criar a comunicação. Revise os dados e tente novamente.",
        ),
      );
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-background/75 p-4 backdrop-blur-sm"
      onClick={handleClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={modalTitleId}
        aria-describedby={modalDescriptionId}
        className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-border bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(false);
          }}
        >
          <div className="flex items-center justify-between border-b border-border px-6 py-5">
            <div>
              <h2
                id={modalTitleId}
                className="text-lg font-bold text-foreground"
              >
                Nova comunicação
              </h2>
              <p
                id={modalDescriptionId}
                className="mt-1 text-xs text-muted-foreground"
              >
                Envie uma mensagem operacional sem incluir conteúdo clínico
                sensível.
              </p>
            </div>
            <button
              type="button"
              onClick={handleClose}
              disabled={create.isPending}
              className={cn(
                "rounded-lg p-2 text-muted-foreground hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50",
                focusRingClass,
              )}
              aria-label="Fechar"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>

          <div className="grid gap-5 p-6 md:grid-cols-2">
            <div className="grid gap-2 text-xs font-semibold text-foreground">
              <label htmlFor={patientSelectId}>Paciente</label>
              <select
                id={patientSelectId}
                className={cn(
                  "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                value={payload.patient_id ?? ""}
                disabled={!requiresPatient || create.isPending}
                onChange={(event) =>
                  update(
                    "patient_id",
                    event.target.value ? Number(event.target.value) : null,
                  )
                }
              >
                <option value="">
                  {requiresPatient
                    ? "Selecione..."
                    : "Não se aplica à notificação interna"}
                </option>
                {patients.data?.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.full_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid gap-2 text-xs font-semibold text-foreground">
              <label htmlFor={recipientSelectId}>Destinatário</label>
              <select
                id={recipientSelectId}
                className={cn(
                  "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                value={payload.recipient_type}
                disabled={!requiresPatient || create.isPending}
                onChange={(event) =>
                  update(
                    "recipient_type",
                    event.target.value as "patient" | "guardian",
                  )
                }
              >
                <option value="patient">
                  {requiresPatient ? "Paciente" : "Usuário conectado"}
                </option>
                {requiresPatient && (
                  <option value="guardian">Responsável legal</option>
                )}
              </select>
            </div>

            <div className="grid gap-2 text-xs font-semibold text-foreground">
              <label htmlFor={channelSelectId}>Canal</label>
              <select
                id={channelSelectId}
                className={cn(
                  "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                value={payload.channel}
                disabled={create.isPending}
                onChange={(event) =>
                  changeChannel(event.target.value as CommunicationChannel)
                }
              >
                {channelOptions.map((channel) => {
                  const config = channels.data?.find(
                    (item) => item.channel === channel,
                  );
                  const ready = Boolean(
                    config?.is_active &&
                    config.connection_status === "configured",
                  );
                  return (
                    <option key={channel} value={channel}>
                      {communicationChannelLabel[channel]}
                      {config && !ready ? " — requer configuração" : ""}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="grid gap-2 text-xs font-semibold text-foreground">
              <label htmlFor={categorySelectId}>Categoria</label>
              <select
                id={categorySelectId}
                className={cn(
                  "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                value={payload.category}
                disabled={create.isPending}
                onChange={(event) =>
                  setPayload((current) => ({
                    ...current,
                    category: event.target.value,
                    template_id: null,
                  }))
                }
              >
                <option value="patient_message">Mensagem ao paciente</option>
                <option value="system_notification">
                  Notificação do sistema
                </option>
                <option value="appointment_confirmation">
                  Confirmação de consulta
                </option>
                <option value="appointment_reminder">Lembrete de consulta</option>
                <option value="form_request">Envio de formulário</option>
                <option value="document_available">Documento disponível</option>
                <option value="payment_due">Aviso financeiro</option>
                <option value="other">Outro</option>
              </select>
            </div>

            {selectedChannelConfig && !selectedChannelReady && (
              <div className="rounded-xl border border-warning/20 bg-warning/5 p-4 text-xs text-muted-foreground md:col-span-2">
                O canal{" "}
                <strong>{communicationChannelLabel[payload.channel]}</strong> está{" "}
                <strong>
                  {communicationConnectionStatusLabel[
                    selectedChannelConfig.connection_status
                  ].toLowerCase()}
                </strong>
                {selectedChannelConfig.is_active ? "." : " e desativado."} Você
                pode salvar como rascunho, mas precisa configurá-lo e ativá-lo
                antes do envio.
              </div>
            )}

            <div className="grid gap-2 text-xs font-semibold text-foreground md:col-span-2">
              <label htmlFor={templateSelectId}>Template</label>
              <select
                id={templateSelectId}
                className={cn(
                  "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                value={payload.template_id ?? ""}
                disabled={create.isPending}
                onChange={(event) =>
                  update(
                    "template_id",
                    event.target.value ? Number(event.target.value) : null,
                  )
                }
              >
                <option value="">Mensagem livre</option>
                {channelTemplates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>

            {!selectedTemplate && (
              <>
                <div className="grid gap-2 text-xs font-semibold text-foreground md:col-span-2">
                  <label htmlFor={subjectInputId}>Assunto</label>
                  <input
                    id={subjectInputId}
                    className={cn(
                      "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                      focusRingClass,
                    )}
                    value={payload.subject}
                    disabled={create.isPending}
                    onChange={(event) => update("subject", event.target.value)}
                    maxLength={255}
                  />
                </div>
                <div className="grid gap-2 text-xs font-semibold text-foreground md:col-span-2">
                  <label htmlFor={bodyTextareaId}>Conteúdo</label>
                  <textarea
                    id={bodyTextareaId}
                    className={cn(
                      "min-h-36 rounded-xl border border-input bg-background p-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                      focusRingClass,
                    )}
                    value={payload.body}
                    disabled={create.isPending}
                    onChange={(event) => update("body", event.target.value)}
                    maxLength={10000}
                    placeholder="Escreva apenas informações administrativas necessárias."
                  />
                </div>
              </>
            )}

            {selectedTemplate && (
              <div className="rounded-xl border border-border bg-secondary/40 p-4 md:col-span-2">
                <p className="text-xs font-bold text-foreground">
                  Preview do template
                </p>
                <p className="mt-2 text-xs font-semibold">
                  {selectedTemplate.subject_template}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-xs text-muted-foreground">
                  {selectedTemplate.body_template}
                </p>
                <p className="mt-3 text-[10px] text-muted-foreground">
                  As variáveis serão preenchidas com dados administrativos
                  autorizados no backend.
                </p>
              </div>
            )}

            <div className="flex items-center gap-3 rounded-xl border border-border p-4 text-xs font-semibold md:col-span-2">
              <input
                id={scheduleCheckboxId}
                type="checkbox"
                className={cn(
                  "rounded border-input text-primary disabled:cursor-not-allowed disabled:opacity-60",
                  focusRingClass,
                )}
                checked={scheduleEnabled}
                disabled={create.isPending}
                onChange={(event) => setScheduleEnabled(event.target.checked)}
              />
              <label htmlFor={scheduleCheckboxId} className="cursor-pointer">
                Agendar envio
              </label>
            </div>

            {scheduleEnabled && (
              <div className="grid gap-2 text-xs font-semibold text-foreground md:col-span-2">
                <label htmlFor={scheduledAtInputId}>Data e hora</label>
                <input
                  id={scheduledAtInputId}
                  type="datetime-local"
                  className={cn(
                    "h-11 rounded-xl border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-60",
                    focusRingClass,
                  )}
                  disabled={create.isPending}
                  onChange={(event) =>
                    update(
                      "scheduled_at",
                      event.target.value
                        ? new Date(event.target.value).toISOString()
                        : null,
                    )
                  }
                />
              </div>
            )}

            <div
              className={cn(
                "rounded-xl border p-4 text-xs text-muted-foreground md:col-span-2",
                selectedChannelReady
                  ? "border-success/20 bg-success/5"
                  : "border-warning/20 bg-warning/5",
              )}
            >
              O backend verificará preferência, consentimento, contato válido,
              configuração do canal e limite do plano antes de aceitar o envio.
              Quando houver bloqueio, a mensagem específica da API será exibida no
              site.
            </div>
          </div>

          <div className="flex flex-wrap justify-end gap-3 border-t border-border px-6 py-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => submit(true)}
              disabled={create.isPending}
            >
              Salvar rascunho
            </Button>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? (
                <Loader2
                  className="mr-2 h-4 w-4 animate-spin"
                  aria-hidden="true"
                />
              ) : (
                <Send className="mr-2 h-4 w-4" aria-hidden="true" />
              )}
              {scheduleEnabled ? "Agendar" : "Enviar"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
