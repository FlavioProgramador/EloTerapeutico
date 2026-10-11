"use client";

import { useEffect, useRef } from "react";
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
  const panelRef = useRef<HTMLDivElement>(null);
  const detail = useCommunication(id);
  const action = useCommunicationAction();

  const isPendingRef = useRef(action.isPending);
  useEffect(() => {
    isPendingRef.current = action.isPending;
  }, [action.isPending]);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isPendingRef.current) {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const items = panelRef.current.querySelectorAll<HTMLElement>(
        "button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex]:not([tabindex='-1'])",
      );
      if (!items.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    const focusTimer = window.setTimeout(
      () =>
        panelRef.current
          ?.querySelector<HTMLElement>("button:not(:disabled)")
          ?.focus(),
      0,
    );

    return () => {
      window.clearTimeout(focusTimer);
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus();
    };
  }, [onClose]);

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
    <div
      className="fixed inset-0 z-50 flex justify-end bg-background/55 backdrop-blur-sm"
      role="presentation"
    >
      <button
        type="button"
        className="flex-1"
        aria-label="Fechar detalhes da comunicação"
        disabled={action.isPending}
        onClick={() => {
          if (!action.isPending) onClose();
        }}
      />
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="communication-drawer-title"
        aria-describedby="communication-drawer-description"
        className="h-full w-full max-w-xl overflow-y-auto border-l border-border bg-card p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="communication-drawer-title" className="text-lg font-bold">
              Detalhes da comunicação
            </h2>
            <p
              id="communication-drawer-description"
              className="mt-1 text-xs text-muted-foreground"
            >
              Histórico imutável, tentativas e destinatário mascarado.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={action.isPending}
            className="rounded-lg p-2 text-muted-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Fechar detalhes"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        {detail.isLoading && (
          <div className="mt-10 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />{" "}
            Carregando...
          </div>
        )}
        {detail.isError && (
          <p className="mt-10 text-sm text-danger" role="alert">
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
                <Button
                  disabled={action.isPending}
                  onClick={() => run("open-manual")}
                >
                  {action.isPending ? (
                    <Loader2
                      className="mr-2 h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <MessageCircle className="mr-2 h-4 w-4" aria-hidden="true" />
                  )}
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
                    disabled={action.isPending}
                    onClick={() => run("mark-manually-sent")}
                  >
                    {action.isPending && (
                      <Loader2
                        className="mr-2 h-4 w-4 animate-spin"
                        aria-hidden="true"
                      />
                    )}
                    Confirmar envio manual
                  </Button>
                )}
              {canRetryCommunication(detail.data.status) && (
                <Button
                  disabled={action.isPending}
                  onClick={() => run("retry")}
                >
                  {action.isPending ? (
                    <Loader2
                      className="mr-2 h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                  ) : (
                    <RefreshCcw className="mr-2 h-4 w-4" aria-hidden="true" />
                  )}
                  Tentar novamente
                </Button>
              )}
              {canCancelCommunication(detail.data.status) && (
                <Button
                  variant="outline"
                  disabled={action.isPending}
                  onClick={() => run("cancel")}
                >
                  {action.isPending && (
                    <Loader2
                      className="mr-2 h-4 w-4 animate-spin"
                      aria-hidden="true"
                    />
                  )}
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
