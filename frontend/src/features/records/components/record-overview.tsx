"use client";

import {
  CalendarCheck2,
  CalendarClock,
  FileText,
  LockKeyhole,
  Sparkles,
  Target,
} from "lucide-react";

import type { RecordSummary } from "../types";

interface RecordOverviewProps {
  summary: RecordSummary;
  onOpenGoal: () => void;
  onOpenDocuments: () => void;
}

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
    },
    {
      label: "Última sessão",
      value: formatDate(summary.last_session),
      helper: summary.last_session ? "atendimento anterior" : "sem sessão anterior",
      icon: CalendarClock,
    },
    {
      label: "Próxima sessão",
      value: formatDate(summary.next_session?.start_time, true),
      helper: summary.next_session ? `${summary.next_session.duration_minutes} minutos` : "não agendada",
      icon: CalendarClock,
    },
    {
      label: "Acompanhamento",
      value: summary.patient.status_display,
      helper: "status cadastral do paciente",
      icon: LockKeyhole,
    },
  ];

  return (
    <section className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4" aria-label="Indicadores do prontuário">
      {items.map((item) => (
        <article key={item.label} className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-start gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <item.icon className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-muted-foreground">{item.label}</p>
              <strong className="mt-1 block truncate text-sm text-foreground">{item.value}</strong>
              <small className="mt-1 block text-[10px] text-muted-foreground">{item.helper}</small>
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
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-bold">Resumo assistido</h3>
          </div>
          <span className="rounded-full bg-secondary px-2 py-0.5 text-[9px] font-bold text-muted-foreground">
            Indisponível
          </span>
        </div>
        <p className="mt-3 text-[11px] leading-5 text-muted-foreground">
          {summary.ai_summary.message}
        </p>
        <button
          type="button"
          disabled
          className="mt-3 w-full rounded-md border border-border bg-secondary/50 px-3 py-2 text-[11px] font-semibold text-muted-foreground opacity-70"
        >
          Geração não configurada
        </button>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-bold">Metas terapêuticas</h3>
          </div>
          <button type="button" onClick={onOpenGoal} className="text-[10px] font-bold text-primary hover:underline">
            Ver todas
          </button>
        </div>
        <div className="mt-4 space-y-4">
          {summary.goals.length === 0 && (
            <p className="text-[11px] leading-5 text-muted-foreground">Nenhuma meta ativa cadastrada.</p>
          )}
          {summary.goals.slice(0, 3).map((goal) => (
            <div key={goal.id}>
              <div className="flex items-center justify-between gap-3 text-[10px]">
                <strong className="truncate text-foreground">{goal.title}</strong>
                <span className="text-muted-foreground">{goal.progress}%</span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-secondary">
                <span className="block h-full rounded-full bg-primary" style={{ width: `${goal.progress}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-primary" />
            <h3 className="text-xs font-bold">Documentos recentes</h3>
          </div>
          <button type="button" onClick={onOpenDocuments} className="text-[10px] font-bold text-primary hover:underline">
            Ver todos
          </button>
        </div>
        <div className="mt-3 space-y-2">
          {summary.recent_documents.length === 0 && (
            <p className="text-[11px] leading-5 text-muted-foreground">Nenhum documento anexado.</p>
          )}
          {summary.recent_documents.slice(0, 3).map((document) => (
            <div key={document.id} className="flex items-start gap-2 rounded-md bg-secondary/50 p-2.5">
              <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
              <div className="min-w-0">
                <strong className="block truncate text-[10px] text-foreground">{document.original_name}</strong>
                <small className="mt-1 block text-[9px] text-muted-foreground">
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
