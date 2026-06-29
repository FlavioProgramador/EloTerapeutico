"use client";

import { useState } from "react";
import { Archive, CheckCircle2, CirclePause, Pencil, Plus, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";
import type { GoalPriority, GoalStatus, TreatmentGoal } from "../types";

interface GoalsTabProps {
  goals: TreatmentGoal[];
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
  evolutions: [],
};

export function GoalsTab({
  goals,
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

  const openCreate = () => {
    setEditing(null);
    setDraft(emptyGoal);
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

  if (loading) return <div className="h-[32rem] animate-pulse rounded-xl bg-secondary" />;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-sm font-bold text-foreground">Plano terapêutico</h3>
          <p className="mt-1 text-[10px] text-muted-foreground">Objetivos, estratégias e progresso vinculados ao acompanhamento.</p>
        </div>
        <Button size="sm" onClick={openCreate} leftIcon={<Plus className="h-4 w-4" />}>
          Nova meta
        </Button>
      </div>

      {goals.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card/40 px-6 py-16 text-center">
          <Target className="mx-auto h-7 w-7 text-muted-foreground" />
          <h4 className="mt-4 text-sm font-bold text-foreground">Nenhuma meta terapêutica</h4>
          <p className="mx-auto mt-2 max-w-md text-xs leading-5 text-muted-foreground">
            Cadastre objetivos para acompanhar estratégias, critérios de avaliação e progresso.
          </p>
        </div>
      ) : (
        <div className="grid gap-3 xl:grid-cols-2">
          {goals.map((goal) => (
            <article key={goal.id} className="rounded-xl border border-border bg-card p-4 shadow-xs">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="truncate text-xs font-bold text-foreground">{goal.title}</h4>
                    <span className={cn(
                      "rounded-full border px-2 py-0.5 text-[8px] font-bold",
                      goal.status === "completed"
                        ? "border-primary/20 bg-primary/10 text-primary"
                        : goal.status === "paused"
                          ? "border-amber-500/20 bg-amber-500/10 text-amber-400"
                          : "border-border bg-secondary text-muted-foreground",
                    )}>
                      {goal.status_display}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[10px] leading-4 text-muted-foreground">
                    {goal.description || "Sem descrição complementar."}
                  </p>
                </div>
                <button type="button" onClick={() => openEdit(goal)} className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground" aria-label={`Editar ${goal.title}`}>
                  <Pencil className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold text-muted-foreground">Progresso</span>
                  <strong className="text-primary">{goal.progress}%</strong>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary">
                  <span className="block h-full rounded-full bg-primary transition-all" style={{ width: `${goal.progress}%` }} />
                </div>
              </div>

              <dl className="mt-4 grid gap-3 border-t border-border pt-4 text-[10px] sm:grid-cols-2">
                <div><dt className="text-muted-foreground">Categoria</dt><dd className="mt-1 font-semibold text-foreground">{goal.category || "Não definida"}</dd></div>
                <div><dt className="text-muted-foreground">Prioridade</dt><dd className="mt-1 font-semibold text-foreground">{goal.priority_display}</dd></div>
                <div className="sm:col-span-2"><dt className="text-muted-foreground">Estratégias</dt><dd className="mt-1 line-clamp-2 font-normal leading-4 text-foreground">{goal.strategies || "Não informadas"}</dd></div>
              </dl>

              <div className="mt-4 flex flex-wrap gap-2">
                {goal.status !== "completed" && (
                  <Button size="sm" variant="outline" onClick={() => onUpdate(goal.id, { status: "completed", progress: 100 })} leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}>
                    Concluir
                  </Button>
                )}
                {goal.status === "active" ? (
                  <Button size="sm" variant="ghost" onClick={() => onUpdate(goal.id, { status: "paused" })} leftIcon={<CirclePause className="h-3.5 w-3.5" />}>
                    Pausar
                  </Button>
                ) : goal.status === "paused" ? (
                  <Button size="sm" variant="ghost" onClick={() => onUpdate(goal.id, { status: "active" })}>
                    Reabrir
                  </Button>
                ) : null}
                <Button size="sm" variant="ghost" onClick={() => window.confirm("Arquivar esta meta?") && onArchive(goal.id)} leftIcon={<Archive className="h-3.5 w-3.5" />}>
                  Arquivar
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? "Editar meta terapêutica" : "Nova meta terapêutica"}
        description="Defina um objetivo observável e os critérios usados para acompanhar sua evolução."
        className="max-w-2xl"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="space-y-1 text-xs font-semibold text-muted-foreground sm:col-span-2">
            Título
            <input value={draft.title ?? ""} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground sm:col-span-2">
            Descrição
            <textarea value={draft.description ?? ""} onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} rows={3} className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground">Categoria
            <input value={draft.category ?? ""} onChange={(event) => setDraft((current) => ({ ...current, category: event.target.value }))} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground">Prioridade
            <select value={draft.priority ?? "medium"} onChange={(event) => setDraft((current) => ({ ...current, priority: event.target.value as GoalPriority }))} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground">
              <option value="low">Baixa</option><option value="medium">Média</option><option value="high">Alta</option>
            </select>
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground">Status
            <select value={draft.status ?? "active"} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as GoalStatus }))} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground">
              <option value="active">Em andamento</option><option value="paused">Pausada</option><option value="completed">Concluída</option>
            </select>
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground">Progresso ({draft.progress ?? 0}%)
            <input type="range" min={0} max={100} value={draft.progress ?? 0} onChange={(event) => setDraft((current) => ({ ...current, progress: Number(event.target.value) }))} className="h-10 w-full accent-primary" />
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground sm:col-span-2">Estratégias e intervenções
            <textarea value={draft.strategies ?? ""} onChange={(event) => setDraft((current) => ({ ...current, strategies: event.target.value }))} rows={3} className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-xs font-semibold text-muted-foreground sm:col-span-2">Critérios de avaliação
            <textarea value={draft.evaluation_criteria ?? ""} onChange={(event) => setDraft((current) => ({ ...current, evaluation_criteria: event.target.value }))} rows={3} className="w-full rounded-md border border-border bg-background p-3 text-xs text-foreground" />
          </label>
        </div>
        <div className="mt-5 flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={() => setModalOpen(false)}>Cancelar</Button>
          <Button isLoading={creating || updating} disabled={!draft.title?.trim()} onClick={save}>Salvar meta</Button>
        </div>
      </Modal>
    </div>
  );
}
