"use client";

import {
  Archive,
  CalendarDays,
  Clock3,
  Copy,
  Edit3,
  FileDown,
  LockKeyhole,
  MapPin,
  Printer,
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { EvolutionWorkspace } from "../types";

interface EvolutionTimelineProps {
  evolutions: EvolutionWorkspace[];
  selected?: EvolutionWorkspace | null;
  loading: boolean;
  onSelect: (id: number) => void;
  onEdit: (evolution: EvolutionWorkspace) => void;
  onDuplicate: (evolution: EvolutionWorkspace) => void;
  onExport: (evolution: EvolutionWorkspace) => void;
}

function formatDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function statusStyles(status: EvolutionWorkspace["status"]) {
  if (status === "finalized") return "border-primary/25 bg-primary/10 text-primary";
  if (status === "archived") return "border-border bg-secondary text-muted-foreground";
  return "border-amber-500/20 bg-amber-500/10 text-amber-400";
}

export function EvolutionTimeline({
  evolutions,
  selected,
  loading,
  onSelect,
  onEdit,
  onDuplicate,
  onExport,
}: EvolutionTimelineProps) {
  if (loading) {
    return (
      <div className="grid gap-3 lg:grid-cols-[minmax(18rem,0.85fr)_minmax(0,1.15fr)]">
        <div className="h-[30rem] animate-pulse rounded-xl bg-secondary" />
        <div className="h-[30rem] animate-pulse rounded-xl bg-secondary" />
      </div>
    );
  }

  if (evolutions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/40 px-6 py-16 text-center">
        <CalendarDays className="mx-auto h-7 w-7 text-muted-foreground" />
        <h3 className="mt-4 text-sm font-bold text-foreground">Nenhuma evolução registrada</h3>
        <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-muted-foreground">
          Crie a primeira evolução clínica para iniciar a linha do tempo do acompanhamento.
        </p>
      </div>
    );
  }

  return (
    <div className="grid min-h-[34rem] gap-3 lg:grid-cols-[minmax(19rem,0.85fr)_minmax(0,1.15fr)]">
      <section className="rounded-xl border border-border bg-card p-3">
        <div className="border-b border-border px-2 pb-3">
          <h3 className="text-xs font-bold text-foreground">Histórico de evoluções</h3>
          <p className="mt-1 text-[10px] text-muted-foreground">Registros em ordem cronológica decrescente</p>
        </div>

        <div className="relative mt-3 space-y-2 before:absolute before:bottom-3 before:left-[1.45rem] before:top-3 before:w-px before:bg-border">
          {evolutions.map((evolution, index) => {
            const active = selected?.id === evolution.id;
            return (
              <button
                key={evolution.id}
                type="button"
                onClick={() => onSelect(evolution.id)}
                className={cn(
                  "relative z-10 grid w-full grid-cols-[2.9rem_1fr] gap-3 rounded-lg border p-3 text-left transition",
                  active
                    ? "border-primary/35 bg-primary/10"
                    : "border-transparent bg-background/40 hover:border-border hover:bg-secondary/60",
                )}
              >
                <span className="grid h-10 w-10 place-items-center rounded-full border border-border bg-card text-[10px] font-bold text-primary">
                  {evolution.session_date.slice(8, 10)}
                  <small className="block text-[8px] font-medium uppercase text-muted-foreground">
                    {new Date(`${evolution.session_date}T12:00:00`).toLocaleDateString("pt-BR", { month: "short" })}
                  </small>
                </span>
                <span className="min-w-0">
                  <span className="flex items-start justify-between gap-2">
                    <strong className="truncate text-xs text-foreground">
                      Sessão {evolutions.length - index}
                    </strong>
                    <span className={cn("rounded-full border px-2 py-0.5 text-[8px] font-bold", statusStyles(evolution.status))}>
                      {evolution.status_display}
                    </span>
                  </span>
                  <span className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted-foreground">
                    {evolution.chief_complaint || evolution.therapist_observations || evolution.content || "Registro clínico sem resumo."}
                  </span>
                  <span className="mt-2 flex flex-wrap gap-2 text-[9px] text-muted-foreground">
                    <span className="inline-flex items-center gap-1"><MapPin className="h-3 w-3" />{evolution.modality === "online" ? "Online" : evolution.modality === "hybrid" ? "Híbrido" : "Presencial"}</span>
                    <span className="inline-flex items-center gap-1"><Clock3 className="h-3 w-3" />{evolution.duration_minutes} min</span>
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="rounded-xl border border-border bg-card p-4">
        {!selected ? (
          <div className="grid h-full min-h-[26rem] place-items-center text-center">
            <div>
              <UserRound className="mx-auto h-7 w-7 text-muted-foreground" />
              <p className="mt-3 text-xs font-semibold text-foreground">Selecione uma evolução</p>
              <p className="mt-1 text-[10px] text-muted-foreground">O conteúdo detalhado aparecerá aqui.</p>
            </div>
          </div>
        ) : (
          <div className="flex h-full flex-col">
            <header className="flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-bold text-foreground">Evolução de {formatDate(selected.session_date)}</h3>
                  {selected.is_locked && <LockKeyhole className="h-3.5 w-3.5 text-muted-foreground" aria-label="Registro bloqueado" />}
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {selected.created_by_name} · {selected.duration_minutes} minutos · versão {Math.max(1, selected.version_count + 1)}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="outline" disabled={!selected.is_editable} onClick={() => onEdit(selected)} leftIcon={<Edit3 className="h-3.5 w-3.5" />}>
                  Editar
                </Button>
                <Button size="sm" variant="outline" onClick={() => onDuplicate(selected)} leftIcon={<Copy className="h-3.5 w-3.5" />}>
                  Duplicar
                </Button>
                <Button size="sm" variant="ghost" onClick={() => onExport(selected)} aria-label="Exportar evolução" title="Exportar evolução">
                  <FileDown className="h-4 w-4" />
                </Button>
                <Button size="sm" variant="ghost" onClick={() => window.print()} aria-label="Imprimir evolução" title="Imprimir evolução">
                  <Printer className="h-4 w-4" />
                </Button>
              </div>
            </header>

            <div className="grid gap-5 py-5 md:grid-cols-2">
              {[
                ["Queixa principal", selected.chief_complaint],
                ["Relato do paciente", selected.patient_report],
                ["Observações clínicas", selected.therapist_observations || selected.content],
                ["Intervenções realizadas", selected.interventions],
                ["Evolução percebida", selected.perceived_evolution],
                ["Tarefas e orientações", selected.homework],
                ["Encaminhamentos", selected.referrals],
                ["Próximos passos", selected.next_steps],
              ].map(([label, value]) => (
                <article key={label} className="rounded-lg bg-background/45 p-3">
                  <h4 className="text-[10px] font-bold uppercase tracking-wide text-primary">{label}</h4>
                  <p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-muted-foreground">
                    {value || "Não informado."}
                  </p>
                </article>
              ))}
            </div>

            <footer className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4 text-[10px] text-muted-foreground">
              <span>Criada em {new Date(selected.created_at).toLocaleString("pt-BR")}</span>
              <span className="inline-flex items-center gap-1">
                <Archive className="h-3 w-3" />
                {selected.addenda_count} aditivo(s) · última edição {new Date(selected.updated_at).toLocaleString("pt-BR")}
              </span>
            </footer>
          </div>
        )}
      </section>
    </div>
  );
}
