"use client";

import {
  CalendarCheck2,
  CalendarClock,
  FileText,
  LockKeyhole,
  Sparkles,
  Target,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { RecordSummary } from "../types";

interface RecordOverviewProps {
  summary: RecordSummary;
  onOpenGoal: () => void;
  onOpenDocuments: () => void;
}

const goalTones = ["bg-primary", "bg-success", "bg-warning"];

function formatDate(value?: string | null, withTime = false) {
  if (!value) return "Não registrada";
  return new Date(value).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

export function RecordStats({ summary }: { summary: RecordSummary }) {
  const items = [
    {
      label: "Sessões registradas",
      value: String(summary.sessions_total),
      helper: "evoluções não arquivadas",
      icon: CalendarCheck2,
      iconTone: "bg-success-soft text-success",
      valueTone: "text-success",
    },
    {
      label: "Última sessão",
      value: formatDate(summary.last_session),
      helper: summary.last_session
        ? "atendimento anterior"
        : "sem sessão anterior",
      icon: CalendarClock,
      iconTone: "bg-primary-soft text-primary",
      valueTone: "text-foreground",
    },
    {
      label: "Próxima sessão",
      value: formatDate(summary.next_session?.start_time, true),
      helper: summary.next_session
        ? `${summary.next_session.duration_minutes} minutos`
        : "não agendada",
      icon: CalendarClock,
      iconTone: "bg-info-soft text-info",
      valueTone: "text-foreground",
    },
    {
      label: "Acompanhamento",
      value: summary.patient.status_display,
      helper: "status cadastral do paciente",
      icon: LockKeyhole,
      iconTone: "bg-secondary text-foreground",
      valueTone: "text-foreground",
    },
  ];

  return (
    <section
      className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4"
      aria-label="Indicadores do prontuário"
    >
      {items.map((item) => (
        <article
          key={item.label}
          className="rounded-xl border border-border bg-card p-4 shadow-xs"
        >
          <div className="flex items-start gap-3">
            <span
              className={cn(
                "grid h-10 w-10 shrink-0 place-items-center rounded-lg",
                item.iconTone,
              )}
            >
              <item.icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-muted-foreground">
                {item.label}
              </p>
              <strong
                className={cn("mt-1 block truncate text-sm", item.valueTone)}
              >
                {item.value}
              </strong>
              <small className="mt-1 block text-xs text-muted-foreground">
                {item.helper}
              </small>
            </div>
          </div>
        </article>
      ))}
    </section>
  );
}

export function RecordSupportPanel({
  summary,
  onOpenGoal,
  onOpenDocuments,
}: RecordOverviewProps) {
  return (
    <aside className="space-y-3" aria-label="Painel de apoio do prontuário">
      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-info-soft text-info">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
            </span>
            <h3 className="text-sm font-semibold">Resumo assistido</h3>
          </div>
          <span className="rounded-full border border-border bg-secondary px-2 py-0.5 text-xs font-semibold text-muted-foreground">
            Indisponível
          </span>
        </div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          {summary.ai_summary.message}
        </p>
        <button
          type="button"
          disabled
          className="mt-3 w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm font-semibold text-muted-foreground opacity-70"
        >
          Recurso indisponível
        </button>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-success-soft text-success">
              <Target className="h-4 w-4" aria-hidden="true" />
            </span>
            <h3 className="text-sm font-semibold">Metas terapêuticas</h3>
          </div>
          <button
            type="button"
            onClick={onOpenGoal}
            className="text-xs font-semibold text-primary hover:text-primary-hover hover:underline"
          >
            Ver todas
          </button>
        </div>
        <div className="mt-4 space-y-4">
          {summary.goals.length === 0 && (
            <p className="text-sm leading-6 text-muted-foreground">
              Nenhuma meta ativa cadastrada.
            </p>
          )}
          {summary.goals.slice(0, 3).map((goal, index) => (
            <div key={goal.id}>
              <div className="flex items-center justify-between gap-3 text-xs">
                <strong className="truncate text-foreground">
                  {goal.title}
                </strong>
                <span className="text-muted-foreground">{goal.progress}%</span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
                <span
                  className={cn(
                    "block h-full rounded-full transition-all",
                    goalTones[index] ?? goalTones[0],
                  )}
                  style={{ width: `${goal.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-primary-soft text-primary">
              <FileText className="h-4 w-4" aria-hidden="true" />
            </span>
            <h3 className="text-sm font-semibold">Documentos recentes</h3>
          </div>
          <button
            type="button"
            onClick={onOpenDocuments}
            className="text-xs font-semibold text-primary hover:text-primary-hover hover:underline"
          >
            Ver todos
          </button>
        </div>
        <div className="mt-3 space-y-2">
          {summary.recent_documents.length === 0 && (
            <p className="text-sm leading-6 text-muted-foreground">
              Nenhum documento anexado.
            </p>
          )}
          {summary.recent_documents.slice(0, 3).map((document) => (
            <div
              key={document.id}
              className="flex items-start gap-2 rounded-md border border-border bg-background p-2.5"
            >
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border border-primary/20 bg-primary-soft text-primary">
                <FileText className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <strong className="block truncate text-xs text-foreground">
                  {document.original_name}
                </strong>
                <small className="mt-1 block text-xs text-muted-foreground">
                  {document.category_display} · {formatDate(document.created_at)}
                </small>
              </div>
            </div>
          ))}
        </div>
      </section>
    </aside>
  );
}
