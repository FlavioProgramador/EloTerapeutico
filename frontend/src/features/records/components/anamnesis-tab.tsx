"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  HeartPulse,
  History,
  Network,
  Pencil,
  Pill,
  Save,
  Sparkles,
  UsersRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AnamnesisWorkspace } from "../types";

interface AnamnesisTabProps {
  data?: AnamnesisWorkspace;
  loading: boolean;
  saving: boolean;
  onSave: (payload: Partial<AnamnesisWorkspace>) => Promise<void>;
  onExport?: () => void;
}

type AnamnesisField = keyof AnamnesisWorkspace;

type SectionDefinition = {
  id: string;
  title: string;
  description: string;
  icon: typeof Activity;
  fields: ReadonlyArray<readonly [AnamnesisField, string]>;
};

const sections: ReadonlyArray<SectionDefinition> = [
  {
    id: "complaint",
    title: "Queixa principal",
    description: "Demanda atual e motivo da busca por atendimento.",
    icon: Sparkles,
    fields: [
      ["chief_complaint", "Queixa principal"],
      ["reason_for_care", "Motivo da busca por atendimento"],
    ],
  },
  {
    id: "clinical",
    title: "Histórico clínico",
    description: "Saúde física, mental e tratamentos anteriores.",
    icon: HeartPulse,
    fields: [
      ["history", "Histórico pessoal e clínico"],
      ["physical_health_history", "Histórico de saúde física"],
      ["mental_health_history", "Histórico psicológico ou psiquiátrico"],
      ["previous_treatments", "Tratamentos anteriores"],
    ],
  },
  {
    id: "family",
    title: "Contexto familiar e social",
    description: "Relações familiares, sociais e rede de convivência.",
    icon: UsersRound,
    fields: [
      ["family_history", "Histórico familiar"],
      ["family_social_relations", "Relações familiares e sociais"],
    ],
  },
  {
    id: "routine",
    title: "Hábitos e rotina",
    description: "Rotina, sono, alimentação e autocuidado.",
    icon: Activity,
    fields: [
      ["habits_and_routine", "Hábitos e rotina"],
      ["sleep", "Sono"],
      ["nutrition", "Alimentação"],
    ],
  },
  {
    id: "assessment",
    title: "Avaliação inicial",
    description: "Impressões iniciais e hipóteses clínicas.",
    icon: CheckCircle2,
    fields: [
      ["initial_assessment", "Avaliação inicial"],
      ["clinical_hypotheses", "Hipóteses clínicas"],
    ],
  },
  {
    id: "medication",
    title: "Medicamentos",
    description: "Uso atual, frequência e observações relevantes.",
    icon: Pill,
    fields: [["medications", "Uso de medicamentos"]],
  },
  {
    id: "life",
    title: "Vida acadêmica e profissional",
    description: "Contextos de estudo, trabalho e desempenho.",
    icon: BookOpen,
    fields: [
      ["academic_history", "Vida acadêmica"],
      ["professional_history", "Vida profissional"],
    ],
  },
  {
    id: "support",
    title: "Rede de apoio e eventos relevantes",
    description: "Pessoas de referência, eventos e observações adicionais.",
    icon: Network,
    fields: [
      ["support_network", "Rede de apoio"],
      ["relevant_events", "Eventos relevantes"],
      ["observations", "Observações adicionais"],
    ],
  },
];

function sectionSummary(
  draft: Partial<AnamnesisWorkspace>,
  fields: SectionDefinition["fields"],
) {
  const firstValue = fields
    .map(([field]) => String(draft[field] ?? "").trim())
    .find(Boolean);
  return firstValue || "Seção ainda não preenchida.";
}

export function AnamnesisTab({
  data,
  loading,
  saving,
  onSave,
  onExport,
}: AnamnesisTabProps) {
  const [selectedSectionId, setSelectedSectionId] = useState<string>(
    sections[0].id,
  );
  const [editing, setEditing] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [draft, setDraft] = useState<Partial<AnamnesisWorkspace>>({});

  useEffect(() => {
    setDraft(data ?? {});
    setDirty(false);
  }, [data]);

  useEffect(() => {
    const warnUnsaved = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnUnsaved);
    return () => window.removeEventListener("beforeunload", warnUnsaved);
  }, [dirty]);

  const selectedSection =
    sections.find((section) => section.id === selectedSectionId) ?? sections[0];

  const completedBySection = useMemo(
    () =>
      Object.fromEntries(
        sections.map((section) => [
          section.id,
          section.fields.filter(([field]) => String(draft[field] ?? "").trim())
            .length,
        ]),
      ),
    [draft],
  );

  const completion = data?.completion_percentage ?? 0;
  const statusLabel =
    data?.status_display ?? (completion === 100 ? "Completa" : "Rascunho");

  const saveSection = async () => {
    const payload = Object.fromEntries(
      selectedSection.fields.map(([field]) => [field, draft[field] ?? ""]),
    ) as Partial<AnamnesisWorkspace>;
    await onSave(payload);
    setDirty(false);
    setEditing(false);
  };

  const cancelEditing = () => {
    setDraft(data ?? {});
    setDirty(false);
    setEditing(false);
  };

  const selectSection = (sectionId: string) => {
    if (
      dirty &&
      !window.confirm("Descartar alterações não salvas desta seção?")
    ) {
      return;
    }
    if (dirty) setDraft(data ?? {});
    setDirty(false);
    setEditing(false);
    setSelectedSectionId(sectionId);
  };

  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17rem]">
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-20 animate-pulse rounded-xl bg-secondary"
            />
          ))}
        </div>
        <div className="h-72 animate-pulse rounded-xl bg-secondary" />
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_17rem]">
      <div className="min-w-0 space-y-3">
        <section className="space-y-2" aria-label="Seções da anamnese">
          {sections.map((section) => {
            const Icon = section.icon;
            const selected = section.id === selectedSection.id;
            const completed = completedBySection[section.id] ?? 0;

            return (
              <button
                key={section.id}
                type="button"
                onClick={() => selectSection(section.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl border px-3.5 py-3 text-left transition",
                  selected
                    ? "border-emerald-400/35 bg-emerald-500/10 shadow-sm"
                    : "border-border bg-card hover:border-emerald-400/20 hover:bg-emerald-500/5",
                )}
              >
                <span
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-lg",
                    selected
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-secondary text-muted-foreground",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-2">
                    <strong className="truncate text-xs text-foreground">
                      {section.title}
                    </strong>
                    <small className="rounded-full border border-emerald-400/15 bg-emerald-500/5 px-1.5 py-0.5 text-[8px] font-bold text-emerald-300">
                      {completed}/{section.fields.length}
                    </small>
                  </span>
                  <small className="mt-1 block truncate text-[10px] text-muted-foreground">
                    {sectionSummary(draft, section.fields)}
                  </small>
                </span>
                <ChevronRight
                  className={cn(
                    "h-4 w-4 shrink-0 transition",
                    selected ? "text-emerald-300" : "text-muted-foreground",
                  )}
                />
              </button>
            );
          })}
        </section>

        <section className="overflow-hidden rounded-xl border border-emerald-400/15 bg-card">
          <header className="flex flex-col gap-3 border-b border-emerald-400/10 bg-emerald-500/5 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="text-xs font-bold text-foreground">
                {selectedSection.title}
              </h3>
              <p className="mt-1 text-[10px] text-muted-foreground">
                {selectedSection.description}
              </p>
            </div>
            {!editing && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setEditing(true)}
                leftIcon={<Pencil className="h-3.5 w-3.5" />}
                className="border-emerald-400/20 text-emerald-200 hover:bg-emerald-500/10"
              >
                Editar seção
              </Button>
            )}
          </header>

          <div className="grid gap-4 p-4 md:grid-cols-2">
            {selectedSection.fields.map(([field, label]) => (
              <label
                key={field}
                className="space-y-1.5 text-[10px] font-semibold text-muted-foreground"
              >
                {label}
                {editing ? (
                  <textarea
                    value={String(draft[field] ?? "")}
                    onChange={(event) => {
                      setDraft((current) => ({
                        ...current,
                        [field]: event.target.value,
                      }));
                      setDirty(true);
                    }}
                    rows={5}
                    className="w-full resize-y rounded-lg border border-border bg-background/80 p-3 text-xs font-normal leading-5 text-foreground outline-none transition focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/10"
                    placeholder={`Registre ${label.toLowerCase()}...`}
                  />
                ) : (
                  <div className="min-h-28 whitespace-pre-wrap rounded-lg border border-border/70 bg-background/40 p-3 text-xs font-normal leading-5 text-muted-foreground">
                    {String(draft[field] ?? "").trim() || "Não informado."}
                  </div>
                )}
              </label>
            ))}
          </div>

          {editing && (
            <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
              <span className="text-[10px] text-muted-foreground">
                {dirty
                  ? "Existem alterações não salvas."
                  : "Nenhuma alteração pendente."}
              </span>
              <div className="flex gap-2">
                <Button size="sm" variant="ghost" onClick={cancelEditing}>
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  isLoading={saving}
                  disabled={!dirty}
                  onClick={saveSection}
                  leftIcon={<Save className="h-3.5 w-3.5" />}
                  className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
                >
                  Salvar seção
                </Button>
              </div>
            </footer>
          )}
        </section>
      </div>

      <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
        <section className="rounded-xl border border-emerald-400/20 bg-gradient-to-b from-emerald-500/10 via-card to-card p-4">
          <h3 className="text-xs font-bold text-foreground">
            Resumo da anamnese
          </h3>
          <p className="mt-1 text-[10px] text-muted-foreground">
            Preenchimento geral
          </p>

          <div className="my-5 flex justify-center">
            <div
              className="grid h-24 w-24 place-items-center rounded-full p-2"
              style={{
                background: `conic-gradient(rgb(52 211 153) ${completion * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
              }}
              aria-label={`${completion}% preenchido`}
            >
              <div className="grid h-full w-full place-items-center rounded-full bg-card">
                <strong className="text-xl text-emerald-300">
                  {completion}%
                </strong>
              </div>
            </div>
          </div>

          <dl className="space-y-3 text-[10px]">
            <div className="flex items-center justify-between gap-3">
              <dt className="text-muted-foreground">Status</dt>
              <dd className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-300">
                {statusLabel}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Última atualização</dt>
              <dd className="mt-1 font-semibold text-foreground">
                {data?.updated_at
                  ? new Date(data.updated_at).toLocaleString("pt-BR")
                  : "Ainda não iniciada"}
              </dd>
            </div>
            {data?.updated_by_name && (
              <div>
                <dt className="text-muted-foreground">
                  Profissional responsável
                </dt>
                <dd className="mt-1 font-semibold text-foreground">
                  {data.updated_by_name}
                </dd>
              </div>
            )}
          </dl>

          <div className="mt-4 grid gap-2 border-t border-emerald-400/10 pt-4">
            <Button
              size="sm"
              onClick={() => setEditing(true)}
              leftIcon={<Pencil className="h-3.5 w-3.5" />}
              className="bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
            >
              Editar seção atual
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={onExport ?? (() => window.print())}
              leftIcon={<Download className="h-3.5 w-3.5" />}
            >
              Exportar PDF
            </Button>
          </div>
        </section>

        <section className="rounded-xl border border-sky-400/15 bg-sky-500/5 p-4 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-2 text-foreground">
            <History className="h-4 w-4 text-sky-300" />
            <strong>Histórico de versões</strong>
          </div>
          <p className="mt-3 leading-4">
            {data?.version_count ?? 0} versão(ões) preservada(s) para auditoria.
          </p>
          <div className="mt-3 flex items-center gap-2 border-t border-sky-400/10 pt-3">
            {data?.updated_at ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
            ) : (
              <Clock3 className="h-3.5 w-3.5 text-amber-300" />
            )}
            <span>
              {data?.updated_at
                ? "Alterações salvas com rastreabilidade."
                : "Anamnese ainda não iniciada."}
            </span>
          </div>
        </section>
      </aside>
    </div>
  );
}
