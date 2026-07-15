"use client";

import { Loader2, MessageCircle, RefreshCcw, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  canCancelCommunication,
  canRetryCommunication,
  communicationChannelLabel as channelLabel,
  communicationStatusLabel as statusLabel,
  isManualWhatsAppReady,
} from "./communications.utils";
import { useCommunication, useCommunicationAction } from "./use-communications";
import { formatDate, statusTone } from "./communications-ui";

export function CommunicationDrawer({
  id,
  onClose,
}: {
  id: string;
  onClose: () => void;
}) {
  const detail = useCommunication(id);
  const action = useCommunicationAction();
  async function run(
    type: "cancel" | "retry" | "mark-manually-sent" | "open-manual",
  ) {
    try {
      const result = (await action.mutateAsync({ id, action: type })) as {
        url?: string;
      };
      if (type === "open-manual" && result.url)
        window.open(result.url, "_blank", "noopener,noreferrer");
      toast.success("Ação registrada.");
    } catch {
      toast.error("Não foi possível concluir esta ação.");
    }
  }
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-background/55 backdrop-blur-sm">
      <button
        type="button"
        className="flex-1"
        aria-label="Fechar detalhes"
        onClick={onClose}
      />
      <aside className="h-full w-full max-w-xl overflow-y-auto border-l border-border bg-card p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold">Detalhes da comunicação</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Histórico imutável, tentativas e destinatário mascarado.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-secondary"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        {detail.isLoading && (
          <div className="mt-10 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Carregando...
          </div>
        )}
        {detail.isError && (
          <p className="mt-10 text-sm text-danger">
            Não foi possível carregar o histórico.
          </p>
        )}
        {detail.data && (
          <div className="mt-6 grid gap-5">
            <div className="flex flex-wrap gap-2">
              <span
                className={cn(
                  "rounded-full border px-3 py-1 text-[11px] font-bold",
                  statusTone(detail.data.status),
                )}
              >
                {statusLabel[detail.data.status]}
              </span>
              <span className="rounded-full border border-border bg-secondary px-3 py-1 text-[11px] font-bold">
                {channelLabel[detail.data.channel]}
              </span>
            </div>
            <div className="rounded-xl border border-border bg-background p-4">
              <p className="text-xs font-bold">
                {detail.data.subject || "Sem assunto"}
              </p>
              <p className="mt-3 whitespace-pre-wrap text-sm text-muted-foreground">
                {detail.data.body}
              </p>
            </div>
            <dl className="grid grid-cols-2 gap-4 rounded-xl border border-border p-4 text-xs">
              <div>
                <dt className="text-muted-foreground">Paciente</dt>
                <dd className="mt-1 font-semibold">
                  {detail.data.patient_name || "Interna"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Destinatário</dt>
                <dd className="mt-1 font-semibold">
                  {detail.data.recipients[0]?.destination_masked || "—"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Criada</dt>
                <dd className="mt-1 font-semibold">
                  {formatDate(detail.data.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Agendada</dt>
                <dd className="mt-1 font-semibold">
                  {formatDate(detail.data.scheduled_at)}
                </dd>
              </div>
            </dl>
            <div>
              <h3 className="text-sm font-bold">Tentativas</h3>
              <div className="mt-3 grid gap-3">
                {detail.data.attempts.length === 0 && (
                  <p className="rounded-xl border border-dashed border-border p-4 text-xs text-muted-foreground">
                    Nenhuma tentativa executada.
                  </p>
                )}
                {detail.data.attempts.map((attempt) => (
                  <div
                    key={attempt.id}
                    className="rounded-xl border border-border p-4 text-xs"
                  >
                    <div className="flex justify-between">
                      <b>Tentativa {attempt.attempt_number}</b>
                      <span>{attempt.status}</span>
                    </div>
                    <p className="mt-2 text-muted-foreground">
                      {attempt.error_message ||
                        `${attempt.provider} processado sem erro técnico exposto.`}
                    </p>
                    <p className="mt-2 text-[10px] text-muted-foreground">
                      {formatDate(attempt.started_at)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {isManualWhatsAppReady(
                detail.data.channel,
                detail.data.status,
                String(detail.data.metadata?.manual_url || ""),
              ) && (
                <Button onClick={() => run("open-manual")}>
                  <MessageCircle className="mr-2 h-4 w-4" />
                  Abrir WhatsApp
                </Button>
              )}
              {isManualWhatsAppReady(
                detail.data.channel,
                detail.data.status,
                String(detail.data.metadata?.manual_url || ""),
              ) &&
                Boolean(detail.data.metadata?.manual_opened_at) && (
                  <Button
                    variant="outline"
                    onClick={() => run("mark-manually-sent")}
                  >
                    Confirmar envio manual
                  </Button>
                )}
              {canRetryCommunication(detail.data.status) && (
                <Button onClick={() => run("retry")}>
                  <RefreshCcw className="mr-2 h-4 w-4" />
                  Tentar novamente
                </Button>
              )}
              {canCancelCommunication(detail.data.status) && (
                <Button variant="outline" onClick={() => run("cancel")}>
                  Cancelar
                </Button>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
