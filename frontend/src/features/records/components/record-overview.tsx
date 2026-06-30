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

const goalTones = ["bg-emerald-400", "bg-sky-400", "bg-amber-400"];
const documentTones = [
  "border-rose-400/20 bg-rose-500/10 text-rose-300",
  "border-sky-400/20 bg-sky-500/10 text-sky-300",
  "border-violet-400/20 bg-violet-500/10 text-violet-300",
];

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
      surface:
        "border-emerald-400/20 bg-gradient-to-br from-emerald-500/10 via-card to-card",
      iconTone: "bg-emerald-500/15 text-emerald-300",
      valueTone: "text-emerald-200",
    },
    {
      label: "Última sessão",
      value: formatDate(summary.last_session),
      helper: summary.last_session
        ? "atendimento anterior"
        : "sem sessão anterior",
      icon: CalendarClock,
      surface:
        "border-sky-400/20 bg-gradient-to-br from-sky-500/10 via-card to-card",
      iconTone: "bg-sky-500/15 text-sky-300",
      valueTone: "text-sky-200",
    },
    {
      label: "Próxima sessão",
      value: formatDate(summary.next_session?.start_time, true),
      helper: summary.next_session
        ? `${summary.next_session.duration_minutes} minutos`
        : "não agendada",
      icon: CalendarClock,
      surface:
        "border-violet-400/20 bg-gradient-to-br from-violet-500/10 via-card to-card",
      iconTone: "bg-violet-500/15 text-violet-300",
      valueTone: "text-violet-200",
    },
    {
      label: "Acompanhamento",
      value: summary.patient.status_display,
      helper: "status cadastral do paciente",
      icon: LockKeyhole,
      surface:
        "border-lime-400/20 bg-gradient-to-br from-lime-500/10 via-card to-card",
      iconTone: "bg-lime-500/15 text-lime-300",
      valueTone: "text-lime-200",
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
          className={cn(
            "rounded-xl border p-4 shadow-xs transition hover:-translate-y-0.5 hover:shadow-md",
            item.surface,
          )}
        >
          <div className="flex items-start gap-3">
            <span
              className={cn(
                "grid h-10 w-10 shrink-0 place-items-center rounded-lg",
                item.iconTone,
              )}
            >
              <item.icon className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-muted-foreground">
                {item.label}
              </p>
              <strong
                className={cn(
                  "mt-1 block truncate text-sm",
                  item.valueTone,
                )}
              >
                {item.value}
              </strong>
              <small className="mt-1 block text-[10px] text-muted-foreground">
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
      <section className="rounded-xl border border-cyan-400/20 bg-gradient-to-br from-cyan-500/10 via-card to-card p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-cyan-500/15 text-cyan-300">
              <Sparkles className="h-4 w-4" />
            </span>
            <h3 className="text-xs font-bold">Resumo assistido</h3>
          </div>
          <span className="rounded-full border border-cyan-400/15 bg-cyan-500/10 px-2 py-0.5 text-[9px] font-bold text-cyan-300">
            Indisponível
          </span>
        </div>
        <p className="mt-3 text-[11px] leading-5 text-muted-foreground">
          {summary.ai_summary.message}
        </p>
        <button
          type="button"
          disabled
          className="mt-3 w-full rounded-md border border-cyan-400/15 bg-cyan-500/5 px-3 py-2 text-[11px] font-semibold text-cyan-200/70 opacity-70"
        >
          Geração não configurada
        </button>
      </section>

      <section className="rounded-xl border border-emerald-400/20 bg-gradient-to-br from-emerald-500/10 via-card to-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-emerald-500/15 text-emerald-300">
              <Target className="h-4 w-4" />
            </span>
            <h3 className="text-xs font-bold">Metas terapêuticas</h3>
          </div>
          <button
            type="button"
            onClick={onOpenGoal}
            className="text-[10px] font-bold text-emerald-300 hover:text-emerald-200 hover:underline"
          >
            Ver todas
          </button>
        </div>
        <div className="mt-4 space-y-4">
          {summary.goals.length === 0 && (
            <p className="text-[11px] leading-5 text-muted-foreground">
              Nenhuma meta ativa cadastrada.
            </p>
          )}
          {summary.goals.slice(0, 3).map((goal, index) => (
            <div key={goal.id}>
              <div className="flex items-center justify-between gap-3 text-[10px]">
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

      <section className="rounded-xl border border-violet-400/20 bg-gradient-to-br from-violet-500/10 via-card to-card p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-md bg-violet-500/15 text-violet-300">
              <FileText className="h-4 w-4" />
            </span>
            <h3 className="text-xs font-bold">Documentos recentes</h3>
          </div>
          <button
            type="button"
            onClick={onOpenDocuments}
            className="text-[10px] font-bold text-violet-300 hover:text-violet-200 hover:underline"
          >
            Ver todos
          </button>
        </div>
        <div className="mt-3 space-y-2">
          {summary.recent_documents.length === 0 && (
            <p className="text-[11px] leading-5 text-muted-foreground">
              Nenhum documento anexado.
            </p>
          )}
          {summary.recent_documents.slice(0, 3).map((document, index) => (
            <div
              key={document.id}
              className="flex items-start gap-2 rounded-md border border-violet-400/10 bg-background/35 p-2.5"
            >
              <span
                className={cn(
                  "mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md border",
                  documentTones[index] ?? documentTones[0],
                )}
              >
                <FileText className="h-3.5 w-3.5" />
              </span>
              <div className="min-w-0">
                <strong className="block truncate text-[10px] text-foreground">
                  {document.original_name}
                </strong>
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
