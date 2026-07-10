"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Loader2, RefreshCw, ShieldAlert } from "lucide-react";

import { getAsaasIntegrationHealth } from "./api";
import type { AsaasIntegrationHealth } from "./types";

function formatDate(value?: string | null) {
  if (!value) return "Nenhum webhook recebido";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function extractStatus(error: unknown) {
  if (typeof error === "object" && error !== null && "response" in error) {
    return (error as { response?: { status?: number } }).response?.status;
  }
  return undefined;
}

export function BillingIntegrationHealth() {
  const [health, setHealth] = useState<AsaasIntegrationHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setHealth(await getAsaasIntegrationHealth());
    } catch (requestError) {
      setHealth(null);
      setError(
        extractStatus(requestError) === 403
          ? "Esta área é restrita a administradores do sistema."
          : "Não foi possível consultar a integração com o Asaas.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[260px] items-center justify-center rounded-3xl border border-border bg-card">
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Verificando integração...
        </div>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="rounded-3xl border border-danger/20 bg-danger-soft p-6 text-danger">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <h2 className="font-bold">Integração indisponível</h2>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className={`grid h-12 w-12 place-items-center rounded-2xl ${health.connected ? "bg-success-soft text-success" : "bg-danger-soft text-danger"}`}>
            {health.connected ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-foreground">Asaas</h2>
              <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${health.connected ? "bg-success-soft text-success" : "bg-danger-soft text-danger"}`}>
                {health.connected ? "Conectado" : "Com falha"}
              </span>
              <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-bold text-muted-foreground">
                {health.environment === "SANDBOX" ? "Sandbox" : "Produção"}
              </span>
            </div>
            <p className="mt-1 text-sm text-muted-foreground">{health.detail}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-sm font-bold hover:bg-muted"
        >
          <RefreshCw className="h-4 w-4" /> Testar conexão
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Metric
          icon={<Activity className="h-5 w-5" />}
          label="Último webhook"
          value={formatDate(health.last_webhook_at)}
        />
        <Metric
          icon={<Loader2 className="h-5 w-5" />}
          label="Eventos pendentes"
          value={String(health.pending_events)}
          warning={health.pending_events > 0}
        />
        <Metric
          icon={<AlertTriangle className="h-5 w-5" />}
          label="Eventos com falha"
          value={String(health.failed_events)}
          warning={health.failed_events > 0}
        />
      </div>

      <div className="rounded-3xl border border-border bg-card p-6 text-sm text-muted-foreground shadow-sm">
        <h3 className="font-bold text-foreground">Operação recomendada</h3>
        <p className="mt-2 leading-6">
          Em produção, mantenha o processamento inline desativado, execute o worker de webhooks continuamente e agende a reconciliação de cobranças. Credenciais e payloads sensíveis não são exibidos nesta tela.
        </p>
      </div>
    </section>
  );
}

function Metric({
  icon,
  label,
  value,
  warning = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  warning?: boolean;
}) {
  return (
    <div className="rounded-3xl border border-border bg-card p-5 shadow-sm">
      <div className={`inline-flex rounded-xl p-2 ${warning ? "bg-warning-soft text-warning" : "bg-primary/10 text-primary"}`}>
        {icon}
      </div>
      <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={`mt-1 text-lg font-extrabold ${warning ? "text-warning" : "text-foreground"}`}>{value}</p>
    </div>
  );
}
