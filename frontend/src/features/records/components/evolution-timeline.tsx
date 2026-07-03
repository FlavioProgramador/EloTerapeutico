"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Archive,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Copy,
  Edit3,
  FileDown,
  Filter,
  History,
  LockKeyhole,
  MapPin,
  Paperclip,
  Printer,
  Search,
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type {
  EvolutionModality,
  EvolutionStatus,
  EvolutionWorkspace,
} from "../types";

interface EvolutionTimelineProps {
  evolutions: EvolutionWorkspace[];
  selected?: EvolutionWorkspace | null;
  loading: boolean;
  onSelect: (id: number) => void;
  onEdit: (evolution: EvolutionWorkspace) => void;
  onDuplicate: (evolution: EvolutionWorkspace) => void;
  onExport: (evolution: EvolutionWorkspace) => void;
}

interface DetailSection {
  label: string;
  value: string;
  tone: "emerald" | "sky" | "violet" | "amber";
}

const PAGE_SIZE = 6;

const dateTones = [
  "border-primary/20 bg-primary/5 text-primary",
  "border-sky-400/30 bg-sky-500/10 text-sky-300",
  "border-violet-400/30 bg-violet-500/10 text-violet-300",
  "border-amber-400/30 bg-amber-500/10 text-amber-300",
];

function formatDate(value: string) {
  return new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatTime(value?: string | null) {
  return value ? value.slice(0, 5) : "Horário não informado";
}

function modalityLabel(modality: EvolutionModality) {
  if (modality === "online") return "Online";
  if (modality === "hybrid") return "Híbrido";
  return "Presencial";
}

function statusStyles(status: EvolutionStatus) {
  if (status === "finalized") {
    return "border-success/20 bg-success/10 text-success";
  }
  if (status === "archived") {
    return "border-border bg-secondary text-muted-foreground";
  }
  return "border-amber-500/20 bg-amber-500/10 text-amber-300";
}

function detailTone(tone: DetailSection["tone"]) {
  return {
    emerald: {
      card: "border-primary/15 bg-primary/5",
      title: "text-primary",
    },
    sky: {
      card: "border-sky-400/15 bg-sky-500/5",
      title: "text-sky-300",
    },
    violet: {
      card: "border-violet-400/15 bg-violet-500/5",
      title: "text-violet-300",
    },
    amber: {
      card: "border-amber-400/15 bg-amber-500/5",
      title: "text-amber-300",
    },
  }[tone];
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
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"all" | EvolutionStatus>("all");
  const [modality, setModality] = useState<"all" | EvolutionModality>("all");
  const [period, setPeriod] = useState("all");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");
    const now = new Date();
    const minimumDate = new Date(now.getTime());
    if (period !== "all") {
      minimumDate.setDate(now.getDate() - Number(period));
    }

    return [...evolutions]
      .filter((evolution) => {
        const searchable = [
          evolution.chief_complaint,
          evolution.patient_report,
          evolution.therapist_observations,
          evolution.content,
          evolution.created_by_name,
        ]
          .join(" ")
          .toLocaleLowerCase("pt-BR");

        const sessionDate = new Date(`${evolution.session_date}T12:00:00`);
        return (
          (!term || searchable.includes(term)) &&
          (status === "all" || evolution.status === status) &&
          (modality === "all" || evolution.modality === modality) &&
          (period === "all" || sessionDate >= minimumDate)
        );
      })
      .sort((first, second) => {
        const difference =
          new Date(first.session_date).getTime() -
          new Date(second.session_date).getTime();
        return order === "asc" ? difference : -difference;
      });
  }, [evolutions, modality, order, period, search, status]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visibleEvolutions = filtered.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  );

  useEffect(() => {
    setPage(1);
  }, [modality, order, period, search, status]);

  if (loading) {
    return (
      <div className="grid gap-3 lg:grid-cols-[minmax(18rem,0.85fr)_minmax(0,1.15fr)]">
        <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />
        <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />
      </div>
    );
  }

  if (evolutions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-primary/20 bg-primary/5 px-6 py-16 text-center">
        <CalendarDays className="mx-auto h-7 w-7 text-primary" />
        <h3 className="mt-4 text-sm font-bold text-foreground">
          Nenhuma evolução registrada
        </h3>
        <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-muted-foreground">
          Crie a primeira evolução clínica para iniciar a linha do tempo do
          acompanhamento.
        </p>
      </div>
    );
  }

  const detailSections: DetailSection[] = selected
    ? [
        {
          label: "Queixa principal",
          value: selected.chief_complaint,
          tone: "emerald",
        },
        {
          label: "Relato do paciente",
          value: selected.patient_report,
          tone: "sky",
        },
        {
          label: "Estado emocional observado",
          value: selected.emotional_state,
          tone: "violet",
        },
        {
          label: "Observações clínicas",
          value: selected.therapist_observations || selected.content,
          tone: "amber",
        },
        {
          label: "Intervenções realizadas",
          value: selected.interventions,
          tone: "emerald",
        },
        {
          label: "Evolução percebida",
          value: selected.perceived_evolution,
          tone: "sky",
        },
        {
          label: "Tarefas e orientações",
          value: selected.homework,
          tone: "violet",
        },
        {
          label: "Encaminhamentos",
          value: selected.referrals,
          tone: "amber",
        },
        {
          label: "Próximos passos",
          value: selected.next_steps,
          tone: "emerald",
        },
      ]
    : [];

  const clearFilters = () => {
    setSearch("");
    setStatus("all");
    setModality("all");
    setPeriod("all");
  };

  return (
    <div className="space-y-3">
      <section className="rounded-xl border border-border bg-card p-3">
        <div className="grid gap-2 md:grid-cols-[minmax(12rem,1fr)_repeat(4,minmax(8rem,auto))]">
          <label className="relative min-w-0">
            <span className="sr-only">Buscar evoluções</span>
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar nas evoluções..."
              className="h-9 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none focus:border-emerald-400/50"
            />
          </label>

          <select
            value={period}
            onChange={(event) => setPeriod(event.target.value)}
            className="h-9 rounded-md border border-border bg-background px-3 text-xs text-foreground"
            aria-label="Filtrar por período"
          >
            <option value="all">Todo o período</option>
            <option value="30">Últimos 30 dias</option>
            <option value="90">Últimos 90 dias</option>
            <option value="365">Último ano</option>
          </select>

          <select
            value={modality}
            onChange={(event) =>
              setModality(event.target.value as "all" | EvolutionModality)
            }
            className="h-9 rounded-md border border-border bg-background px-3 text-xs text-foreground"
            aria-label="Filtrar por modalidade"
          >
            <option value="all">Todas as modalidades</option>
            <option value="in_person">Presencial</option>
            <option value="online">Online</option>
            <option value="hybrid">Híbrido</option>
          </select>

          <select
            value={status}
            onChange={(event) =>
              setStatus(event.target.value as "all" | EvolutionStatus)
            }
            className="h-9 rounded-md border border-border bg-background px-3 text-xs text-foreground"
            aria-label="Filtrar por status"
          >
            <option value="all">Todos os status</option>
            <option value="draft">Rascunho</option>
            <option value="finalized">Finalizada</option>
            <option value="archived">Arquivada</option>
          </select>

          <button
            type="button"
            onClick={() =>
              setOrder((current) => (current === "desc" ? "asc" : "desc"))
            }
            className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-border bg-background px-3 text-xs text-muted-foreground hover:bg-secondary"
          >
            <Filter className="h-3.5 w-3.5" />
            {order === "desc" ? "Mais recentes" : "Mais antigas"}
          </button>
        </div>
      </section>

      <div className="grid min-h-[34rem] gap-3 lg:grid-cols-[minmax(20rem,0.85fr)_minmax(0,1.15fr)]">
        <section className="flex min-h-[34rem] flex-col rounded-xl border border-emerald-400/15 bg-gradient-to-b from-emerald-500/5 via-card to-card p-3">
          <header className="border-b border-emerald-400/15 px-2 pb-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <h3 className="text-xs font-bold text-foreground">
                    Histórico de evoluções
                  </h3>
                </div>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {filtered.length} registro(s) localizado(s)
                </p>
              </div>
              {(search ||
                status !== "all" ||
                modality !== "all" ||
                period !== "all") && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="text-[9px] font-semibold text-primary hover:underline"
                >
                  Limpar filtros
                </button>
              )}
            </div>
          </header>

          {filtered.length === 0 ? (
            <div className="grid flex-1 place-items-center px-5 py-14 text-center">
              <div>
                <Search className="mx-auto h-6 w-6 text-muted-foreground" />
                <p className="mt-3 text-xs font-semibold text-foreground">
                  Nenhuma evolução encontrada
                </p>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  Ajuste os filtros ou o termo pesquisado.
                </p>
              </div>
            </div>
          ) : (
            <div className="relative mt-3 flex-1 space-y-2 before:absolute before:bottom-3 before:left-[1.45rem] before:top-3 before:w-px before:bg-primary/20">
              {visibleEvolutions.map((evolution, index) => {
                const active = selected?.id === evolution.id;
                const sessionNumber =
                  evolutions.findIndex((item) => item.id === evolution.id) + 1;

                return (
                  <button
                    key={evolution.id}
                    type="button"
                    onClick={() => onSelect(evolution.id)}
                    className={cn(
                      "relative z-10 grid w-full grid-cols-[2.9rem_1fr] gap-3 rounded-lg border p-3 text-left transition",
                      active
                        ? "border-primary/30 bg-gradient-to-r from-primary/10 to-accent/5 shadow-sm"
                        : "border-transparent bg-background/35 hover:border-sky-400/15 hover:bg-sky-500/5",
                    )}
                  >
                    <span
                      className={cn(
                        "grid h-10 w-10 place-items-center rounded-full border text-[10px] font-bold",
                        active
                          ? "border-primary/30 bg-primary/10 text-primary"
                          : dateTones[index % dateTones.length],
                      )}
                    >
                      {evolution.session_date.slice(8, 10)}
                      <small className="block text-[8px] font-medium uppercase text-muted-foreground">
                        {new Date(
                          `${evolution.session_date}T12:00:00`,
                        ).toLocaleDateString("pt-BR", { month: "short" })}
                      </small>
                    </span>

                    <span className="min-w-0">
                      <span className="flex items-start justify-between gap-2">
                        <strong className="truncate text-xs text-foreground">
                          Sessão {sessionNumber}
                        </strong>
                        <span
                          className={cn(
                            "rounded-full border px-2 py-0.5 text-[8px] font-bold",
                            statusStyles(evolution.status),
                          )}
                        >
                          {evolution.status_display}
                        </span>
                      </span>
                      <span className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted-foreground">
                        {evolution.chief_complaint ||
                          evolution.therapist_observations ||
                          evolution.content ||
                          "Registro clínico sem resumo."}
                      </span>
                      <span className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-sky-300" />
                          {modalityLabel(evolution.modality)}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <Clock3 className="h-3 w-3 text-violet-300" />
                          {formatTime(evolution.session_time)} ·{" "}
                          {evolution.duration_minutes} min
                        </span>
                        {(evolution.attached_documents_count ?? 0) > 0 && (
                          <span className="inline-flex items-center gap-1">
                            <Paperclip className="h-3 w-3 text-amber-300" />
                            {evolution.attached_documents_count} anexo(s)
                          </span>
                        )}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {filtered.length > PAGE_SIZE && (
            <footer className="mt-3 flex items-center justify-between border-t border-emerald-400/10 px-2 pt-3 text-[9px] text-muted-foreground">
              <span>
                Página {page} de {totalPages}
              </span>
              <div className="flex gap-1">
                <button
                  type="button"
                  disabled={page === 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  className="grid h-7 w-7 place-items-center rounded-md border border-border disabled:opacity-40"
                  aria-label="Página anterior"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() =>
                    setPage((current) => Math.min(totalPages, current + 1))
                  }
                  className="grid h-7 w-7 place-items-center rounded-md border border-border disabled:opacity-40"
                  aria-label="Próxima página"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </footer>
          )}
        </section>

        <section className="rounded-xl border border-sky-400/15 bg-gradient-to-br from-sky-500/5 via-card to-card p-4">
          {!selected ? (
            <div className="grid h-full min-h-[26rem] place-items-center text-center">
              <div>
                <UserRound className="mx-auto h-7 w-7 text-sky-300" />
                <p className="mt-3 text-xs font-semibold text-foreground">
                  Selecione uma evolução
                </p>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  O conteúdo detalhado aparecerá aqui.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex h-full flex-col">
              <header className="flex flex-col gap-3 border-b border-sky-400/15 pb-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-sm font-bold text-foreground">
                      Evolução de {formatDate(selected.session_date)}
                    </h3>
                    <span
                      className={cn(
                        "rounded-full border px-2 py-0.5 text-[8px] font-bold",
                        statusStyles(selected.status),
                      )}
                    >
                      {selected.status_display}
                    </span>
                    {selected.is_locked && (
                      <LockKeyhole
                        className="h-3.5 w-3.5 text-amber-300"
                        aria-label="Registro bloqueado"
                      />
                    )}
                  </div>
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    {selected.created_by_name} · {formatTime(selected.session_time)} ·{" "}
                    {selected.duration_minutes} minutos · versão{" "}
                    {Math.max(1, selected.version_count + 1)}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!selected.is_editable}
                    onClick={() => onEdit(selected)}
                    leftIcon={<Edit3 className="h-3.5 w-3.5" />}
                    className="border-primary/20 text-primary hover:bg-primary/10"
                  >
                    Editar
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onDuplicate(selected)}
                    leftIcon={<Copy className="h-3.5 w-3.5" />}
                    className="border-violet-400/20 text-violet-200 hover:bg-violet-500/10 hover:text-violet-100"
                  >
                    Duplicar
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onExport(selected)}
                    aria-label="Exportar evolução"
                    title="Exportar evolução"
                    className="text-sky-300 hover:bg-sky-500/10 hover:text-sky-200"
                  >
                    <FileDown className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => window.print()}
                    aria-label="Imprimir evolução"
                    title="Imprimir evolução"
                    className="text-amber-300 hover:bg-amber-500/10 hover:text-amber-200"
                  >
                    <Printer className="h-4 w-4" />
                  </Button>
                </div>
              </header>

              <div className="grid gap-3 py-4 md:grid-cols-2">
                {detailSections.map((section) => {
                  const tone = detailTone(section.tone);
                  return (
                    <article
                      key={section.label}
                      className={cn("rounded-lg border p-3", tone.card)}
                    >
                      <h4
                        className={cn(
                          "text-[10px] font-bold uppercase tracking-wide",
                          tone.title,
                        )}
                      >
                        {section.label}
                      </h4>
                      <div className="mt-2">
                        <SafeMarkdownRenderer content={section.value} />
                      </div>
                    </article>
                  );
                })}
              </div>

              <div className="grid gap-3 border-t border-sky-400/15 py-4 sm:grid-cols-3">
                <div className="rounded-lg bg-background/35 p-3">
                  <div className="flex items-center gap-2 text-sky-300">
                    <UserRound className="h-3.5 w-3.5" />
                    <strong className="text-[10px]">Autoria</strong>
                  </div>
                  <p className="mt-2 text-[10px] text-muted-foreground truncate">
                    {selected.created_by_name}
                  </p>
                </div>
                <div className="rounded-lg bg-background/35 p-3">
                  <div className="flex items-center gap-2 text-violet-300">
                    <MapPin className="h-3.5 w-3.5" />
                    <strong className="text-[10px]">Modalidade</strong>
                  </div>
                  <p className="mt-2 text-[10px] text-muted-foreground">
                    {modalityLabel(selected.modality)} · {selected.duration_minutes} min.
                  </p>
                </div>
                <div className="rounded-lg bg-background/35 p-3">
                  <div className="flex items-center gap-2 text-amber-300">
                    <History className="h-3.5 w-3.5" />
                    <strong className="text-[10px]">Versões</strong>
                  </div>
                  <p className="mt-2 text-[10px] text-muted-foreground">
                    {selected.version_count} versão(ões) anterior(es).
                  </p>
                </div>
              </div>

              <footer className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-sky-400/15 pt-4 text-[10px] text-muted-foreground">
                <span>
                  Criada em {new Date(selected.created_at).toLocaleString("pt-BR")}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Archive className="h-3 w-3 text-violet-300" />
                  {selected.addenda_count} aditivo(s) · última edição{" "}
                  {new Date(selected.updated_at).toLocaleString("pt-BR")}
                </span>
              </footer>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function SafeMarkdownRenderer({ content }: { content: string }) {
  if (!content) return <span className="text-xs text-muted-foreground">Não informado.</span>;
  
  const escaped = content
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

  const html = escaped
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
  
  const lines = html.split("\n");
  const processedLines = lines.map((line) => {
    const stripped = line.trim();
    if (stripped.startsWith("- ")) {
      return `<li class="list-disc list-inside ml-2 text-xs leading-5">${stripped.substring(2)}</li>`;
    }
    if (/^\d+\.\s/.test(stripped)) {
      return `<li class="list-decimal list-inside ml-2 text-xs leading-5">${stripped.replace(/^\d+\.\s/, "")}</li>`;
    }
    return stripped ? `<p class="mt-1 text-xs leading-5">${stripped}</p>` : "";
  });

  const finalHtml = processedLines.join("");
  return <div className="text-xs leading-5 text-muted-foreground" dangerouslySetInnerHTML={{ __html: finalHtml }} />;
}
