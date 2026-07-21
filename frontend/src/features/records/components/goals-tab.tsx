"use client";

import { useMemo, useState, useId } from "react";
import {
  Archive,
  ArrowDown,
  ArrowUp,
  CalendarClock,
  CheckCircle2,
  CirclePause,
  Eye,
  Pencil,
  Plus,
  RotateCcw,
  ShieldCheck,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";
import type {
  GoalPriority,
  GoalStatus,
  RecordSummary,
  TreatmentGoal,
} from "../types";

interface GoalsTabProps {
  goals: TreatmentGoal[];
  summary: RecordSummary;
  loading: boolean;
  creating: boolean;
  updating: boolean;
  onCreate: (payload: Partial<TreatmentGoal>) => Promise<void>;
  onUpdate: (id: number, payload: Partial<TreatmentGoal>) => Promise<void>;
  onArchive: (id: number) => Promise<void>;
}

const emptyGoal: Partial<TreatmentGoal> = {
  title: "",
  description: "",
  category: "",
  priority: "medium",
  status: "active",
  progress: 0,
  strategies: "",
  evaluation_criteria: "",
  observations: "",
  start_date: new Date().toISOString().slice(0, 10),
  target_date: null,
  evolutions: [],
};

function statusTone(status: GoalStatus) {
  if (status === "completed") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-300";
  }
  if (status === "paused") {
    return "border-amber-400/20 bg-amber-500/10 text-amber-300";
  }
  if (status === "archived") {
    return "border-border bg-secondary text-muted-foreground";
  }
  return "border-sky-400/20 bg-sky-500/10 text-sky-300";
}

function priorityTone(priority: GoalPriority) {
  if (priority === "high") return "text-rose-300";
  if (priority === "low") return "text-sky-300";
  return "text-amber-300";
}

export function GoalsTab({
  goals,
  summary,
  loading,
  creating,
  updating,
  onCreate,
  onUpdate,
  onArchive,
}: GoalsTabProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TreatmentGoal | null>(null);
  const [draft, setDraft] = useState<Partial<TreatmentGoal>>(emptyGoal);

  const baseId = useId();
  const titleId = `${baseId}-title`;
  const descriptionId = `${baseId}-description`;
  const categoryId = `${baseId}-category`;
  const priorityId = `${baseId}-priority`;
  const startDateId = `${baseId}-start-date`;
  const targetDateId = `${baseId}-target-date`;
  const statusId = `${baseId}-status`;
  const progressId = `${baseId}-progress`;
  const strategiesId = `${baseId}-strategies`;
  const evaluationCriteriaId = `${baseId}-evaluation-criteria`;
  const observationsId = `${baseId}-observations`;

  const visibleGoals = useMemo(
    () => goals.filter((goal) => goal.status !== "archived"),
    [goals],
  );
  const mainGoal =
    visibleGoals.find((goal) => goal.status === "active") ?? visibleGoals[0];
  const activeCount = visibleGoals.filter((goal) => goal.status === "active").length;
  const completedCount = visibleGoals.filter(
    (goal) => goal.status === "completed",
  ).length;
  const overallProgress = visibleGoals.length
    ? Math.round(
        visibleGoals.reduce((total, goal) => total + goal.progress, 0) /
          visibleGoals.length,
      )
    : 0;

  const openCreate = () => {
    setEditing(null);
    setDraft({ ...emptyGoal, sort_order: visibleGoals.length });
    setModalOpen(true);
  };

  const openEdit = (goal: TreatmentGoal) => {
    setEditing(goal);
    setDraft(goal);
    setModalOpen(true);
  };

  const save = async () => {
    if (!draft.title?.trim()) return;
    if (editing) await onUpdate(editing.id, draft);
    else await onCreate(draft);
    setModalOpen(false);
  };

  const moveGoal = async (goal: TreatmentGoal, direction: -1 | 1) => {
    const currentIndex = visibleGoals.findIndex((item) => item.id === goal.id);
    const target = visibleGoals[currentIndex + direction];
    if (!target) return;
    await Promise.all([
      onUpdate(goal.id, { sort_order: target.sort_order }),
      onUpdate(target.id, { sort_order: goal.sort_order }),
    ]);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <div className="h-24 animate-pulse rounded-xl bg-secondary" />
          <div className="h-24 animate-pulse rounded-xl bg-secondary" />
        </div>
        <div className="h-[28rem] animate-pulse rounded-xl bg-secondary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_17rem]">
        <section className="rounded-xl border border-emerald-400/20 bg-gradient-to-br from-emerald-500/10 via-card to-card p-4">
          <div className="flex items-start gap-3">
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-emerald-500/15 text-emerald-300">
              <Target className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-300">
                Objetivo principal
              </p>
              <h3 className="mt-1 text-sm font-bold text-foreground">
                {mainGoal?.title ?? "Nenhum objetivo principal definido"}
              </h3>
              <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted-foreground">
                {mainGoal?.description ||
                  "Cadastre uma meta para definir o objetivo principal do acompanhamento."}
              </p>
              {mainGoal && (
                <div className="mt-3 flex flex-wrap gap-3 text-[9px] text-muted-foreground">
                  <span>Status: {mainGoal.status_display}</span>
                  <span>Início: {new Date(`${mainGoal.start_date}T12:00:00`).toLocaleDateString("pt-BR")}</span>
                  {mainGoal.created_by_name && <span>Responsável: {mainGoal.created_by_name}</span>}
                </div>
              )}
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-sky-400/20 bg-sky-500/5 p-4">
          <div className="flex items-center gap-2 text-sky-300">
            <CalendarClock className="h-4 w-4" />
            <h3 className="text-xs font-bold text-foreground">Próxima revisão</h3>
          </div>
          {summary.next_session ? (
            <>
              <strong className="mt-3 block text-sm text-sky-200">
                {new Date(summary.next_session.start_time).toLocaleDateString("pt-BR")}
              </strong>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {new Date(summary.next_session.start_time).toLocaleString("pt-BR", {
                  weekday: "long",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </>
          ) : (
            <p className="mt-3 text-[10px] leading-4 text-muted-foreground">
              Nenhuma revisão ou sessão futura agendada.
            </p>
          )}
        </section>
      </div>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_17rem]">
        <section className="rounded-xl border border-border bg-card">
          <header className="flex flex-col gap-3 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-xs font-bold text-foreground">Metas terapêuticas</h3>
              <p className="mt-1 text-[10px] text-muted-foreground">
                Objetivos, estratégias, prioridade e progresso do acompanhamento.
              </p>
            </div>
            <Button
              size="sm"
              onClick={openCreate}
              leftIcon={<Plus className="h-4 w-4" />}
              className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
            >
              Nova meta
            </Button>
          </header>

          {visibleGoals.length === 0 ? (
            <div className="px-6 py-14 text-center">
              <Target className="mx-auto h-7 w-7 text-emerald-300" />
              <h4 className="mt-4 text-sm font-bold text-foreground">
                Nenhuma meta terapêutica
              </h4>
              <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-muted-foreground">
                Cadastre objetivos para acompanhar estratégias, critérios e evolução.
              </p>
              <Button size="sm" className="mt-4" onClick={openCreate}>
                Criar primeira meta
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {visibleGoals.map((goal, index) => (
                <article key={goal.id} className="px-4 py-4">
                  <div className="flex items-start gap-3">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-emerald-500/10 text-emerald-300">
                      {goal.status === "completed" ? (
                        <ShieldCheck className="h-4 w-4" />
                      ) : (
                        <Target className="h-4 w-4" />
                      )}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="truncate text-xs font-bold text-foreground">
                          {goal.title}
                        </h4>
                        <span className={cn("rounded-full border px-2 py-0.5 text-[8px] font-bold", statusTone(goal.status))}>
                          {goal.status_display}
                        </span>
                        <span className={cn("text-[9px] font-semibold", priorityTone(goal.priority))}>
                          Prioridade {goal.priority_display.toLowerCase()}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-muted-foreground">
                        {goal.description || "Sem descrição complementar."}
                      </p>

                      <div className="mt-3">
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-muted-foreground">Progresso</span>
                          <strong className="text-emerald-300">{goal.progress}%</strong>
                        </div>
                        <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-secondary">
                          <span
                            className="block h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 transition-all"
                            style={{ width: `${goal.progress}%` }}
                          />
                        </div>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[9px] text-muted-foreground">
                        <span>Início: {new Date(`${goal.start_date}T12:00:00`).toLocaleDateString("pt-BR")}</span>
                        <span>
                          Prazo: {goal.target_date ? new Date(`${goal.target_date}T12:00:00`).toLocaleDateString("pt-BR") : "não definido"}
                        </span>
                        <span>{goal.evolutions.length} evolução(ões) vinculada(s)</span>
                      </div>
                    </div>

                    <div className="flex shrink-0 gap-1">
                      <button
                        type="button"
                        disabled={index === 0}
                        onClick={() => moveGoal(goal, -1)}
                        className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                        aria-label="Mover meta para cima"
                      >
                        <ArrowUp className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        disabled={index === visibleGoals.length - 1}
                        onClick={() => moveGoal(goal, 1)}
                        className="rounded-md p-1.5 text-muted-foreground hover:bg-secondary disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                        aria-label="Mover meta para baixo"
                      >
                        <ArrowDown className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => openEdit(goal)}
                        className="rounded-md p-1.5 text-emerald-300 hover:bg-emerald-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                        aria-label={`Editar ${goal.title}`}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2 pl-12">
                    {goal.status !== "completed" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onUpdate(goal.id, { status: "completed", progress: 100 })}
                        leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                        className="border-emerald-400/20 text-emerald-200 hover:bg-emerald-500/10"
                      >
                        Concluir
                      </Button>
                    )}
                    {goal.status === "active" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onUpdate(goal.id, { status: "paused" })}
                        leftIcon={<CirclePause className="h-3.5 w-3.5" />}
                      >
                        Pausar
                      </Button>
                    )}
                    {goal.status === "paused" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onUpdate(goal.id, { status: "active" })}
                        leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
                      >
                        Reabrir
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        window.confirm("Arquivar esta meta terapêutica?") && onArchive(goal.id)
                      }
                      leftIcon={<Archive className="h-3.5 w-3.5" />}
                    >
                      Arquivar
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="space-y-3 xl:sticky xl:top-4">
          <section className="rounded-xl border border-emerald-400/20 bg-gradient-to-b from-emerald-500/10 via-card to-card p-4">
            <h3 className="text-xs font-bold text-foreground">Evolução geral</h3>
            <p className="mt-1 text-[10px] text-muted-foreground">Progresso médio do plano</p>
            <div className="my-5 flex justify-center">
              <div
                className="grid h-24 w-24 place-items-center rounded-full p-2"
                style={{
                  background: `conic-gradient(rgb(52 211 153) ${overallProgress * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
                }}
              >
                <div className="grid h-full w-full place-items-center rounded-full bg-card">
                  <strong className="text-xl text-emerald-300">{overallProgress}%</strong>
                </div>
              </div>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-center text-[10px]">
              <div className="rounded-lg bg-emerald-500/5 p-2">
                <dt className="text-muted-foreground">Ativas</dt>
                <dd className="mt-1 text-sm font-bold text-emerald-300">{activeCount}</dd>
              </div>
              <div className="rounded-lg bg-sky-500/5 p-2">
                <dt className="text-muted-foreground">Concluídas</dt>
                <dd className="mt-1 text-sm font-bold text-sky-300">{completedCount}</dd>
              </div>
            </dl>
            <Button
              size="sm"
              variant="outline"
              className="mt-3 w-full"
              leftIcon={<Eye className="h-3.5 w-3.5" />}
              onClick={() => window.print()}
            >
              Visualizar evolução
            </Button>
          </section>
        </aside>
      </div>

      <section className="overflow-hidden rounded-xl border border-border bg-card">
        <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div>
            <h3 className="text-xs font-bold text-foreground">Intervenções terapêuticas</h3>
            <p className="mt-1 text-[10px] text-muted-foreground">
              Estratégias registradas nas metas e seus responsáveis.
            </p>
          </div>
        </header>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[42rem] text-left text-[10px]">
            <thead className="bg-background/40 text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Intervenção</th>
                <th className="px-4 py-2.5 font-semibold">Meta vinculada</th>
                <th className="px-4 py-2.5 font-semibold">Responsável</th>
                <th className="px-4 py-2.5 font-semibold">Status</th>
                <th className="px-4 py-2.5 text-right font-semibold">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {visibleGoals.map((goal) => (
                <tr key={goal.id} className="hover:bg-emerald-500/5">
                  <td className="max-w-sm px-4 py-3 text-foreground">
                    <span className="line-clamp-2">
                      {goal.strategies || "Estratégia ainda não informada."}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{goal.title}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {goal.created_by_name || "Terapeuta responsável"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("rounded-full border px-2 py-0.5 text-[8px] font-bold", statusTone(goal.status))}>
                      {goal.status_display}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => openEdit(goal)}
                      className="rounded-md p-1.5 text-emerald-300 hover:bg-emerald-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
                      aria-label={`Editar intervenção de ${goal.title}`}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {visibleGoals.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-10 text-center text-muted-foreground">
                    Nenhuma intervenção registrada nas metas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar meta terapêutica" : "Nova meta terapêutica"}
        description="Defina um objetivo observável, prazo, progresso e estratégias clínicas."
        className="max-w-2xl"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor={titleId} className="text-xs font-semibold text-muted-foreground">
              Título
            </label>
            <input
              id={titleId}
              value={draft.title ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor={descriptionId} className="text-xs font-semibold text-muted-foreground">
              Descrição
            </label>
            <textarea
              id={descriptionId}
              value={draft.description ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
              rows={3}
              className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={categoryId} className="text-xs font-semibold text-muted-foreground">
              Categoria
            </label>
            <input
              id={categoryId}
              value={draft.category ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={priorityId} className="text-xs font-semibold text-muted-foreground">
              Prioridade
            </label>
            <select
              id={priorityId}
              value={draft.priority ?? "medium"}
              onChange={(event) => setDraft((current) => ({ ...current, priority: event.target.value as GoalPriority }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <option value="low">Baixa</option>
              <option value="medium">Média</option>
              <option value="high">Alta</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label htmlFor={startDateId} className="text-xs font-semibold text-muted-foreground">
              Data de início
            </label>
            <input
              id={startDateId}
              type="date"
              value={draft.start_date ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, start_date: event.target.value }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={targetDateId} className="text-xs font-semibold text-muted-foreground">
              Prazo estimado
            </label>
            <input
              id={targetDateId}
              type="date"
              value={draft.target_date ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, target_date: event.target.value || null }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor={statusId} className="text-xs font-semibold text-muted-foreground">
              Status
            </label>
            <select
              id={statusId}
              value={draft.status ?? "active"}
              onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as GoalStatus }))}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <option value="active">Em andamento</option>
              <option value="paused">Pausada</option>
              <option value="completed">Concluída</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label htmlFor={progressId} className="text-xs font-semibold text-muted-foreground">
              Progresso ({draft.progress ?? 0}%)
            </label>
            <input
              id={progressId}
              type="range"
              min={0}
              max={100}
              value={draft.progress ?? 0}
              onChange={(event) => setDraft((current) => ({ ...current, progress: Number(event.target.value) }))}
              className="h-10 w-full accent-emerald-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor={strategiesId} className="text-xs font-semibold text-muted-foreground">
              Estratégias e intervenções
            </label>
            <textarea
              id={strategiesId}
              value={draft.strategies ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, strategies: event.target.value }))}
              rows={3}
              className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor={evaluationCriteriaId} className="text-xs font-semibold text-muted-foreground">
              Critérios de avaliação
            </label>
            <textarea
              id={evaluationCriteriaId}
              value={draft.evaluation_criteria ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, evaluation_criteria: event.target.value }))}
              rows={3}
              className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <label htmlFor={observationsId} className="text-xs font-semibold text-muted-foreground">
              Observações
            </label>
            <textarea
              id={observationsId}
              value={draft.observations ?? ""}
              onChange={(event) => setDraft((current) => ({ ...current, observations: event.target.value }))}
              rows={2}
              className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={() => setModalOpen(false)}>
            Cancelar
          </Button>
          <Button
            isLoading={creating || updating}
            disabled={!draft.title?.trim()}
            onClick={save}
            className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
          >
            Salvar meta
          </Button>
        </div>
      </Modal>
    </div>
  );
}
