"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Clock3, History, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { AnamnesisWorkspace } from "../types";

interface AnamnesisTabProps {
  data?: AnamnesisWorkspace;
  loading: boolean;
  saving: boolean;
  onSave: (payload: Partial<AnamnesisWorkspace>) => Promise<void>;
}

const sections = [
  {
    id: "initial",
    title: "Demanda e avaliação inicial",
    description: "Motivo da busca, queixa principal e primeira avaliação.",
    fields: [
      ["chief_complaint", "Queixa principal"],
      ["reason_for_care", "Motivo da busca por atendimento"],
      ["initial_assessment", "Avaliação inicial"],
      ["clinical_hypotheses", "Hipóteses clínicas"],
    ],
  },
  {
    id: "health",
    title: "Saúde e tratamentos",
    description: "Histórico físico, mental, medicações e tratamentos anteriores.",
    fields: [
      ["physical_health_history", "Histórico de saúde física"],
      ["mental_health_history", "Histórico de saúde mental"],
      ["medications", "Uso de medicamentos"],
      ["previous_treatments", "Tratamentos anteriores"],
    ],
  },
  {
    id: "history",
    title: "História pessoal e familiar",
    description: "Eventos relevantes, histórico pessoal e contexto familiar.",
    fields: [
      ["history", "Histórico pessoal"],
      ["family_history", "Histórico familiar"],
      ["relevant_events", "Eventos relevantes"],
      ["family_social_relations", "Relações familiares e sociais"],
    ],
  },
  {
    id: "routine",
    title: "Hábitos, rotina e rede de apoio",
    description: "Sono, alimentação, rotina e relações de suporte.",
    fields: [
      ["habits_and_routine", "Hábitos e rotina"],
      ["sleep", "Sono"],
      ["nutrition", "Alimentação"],
      ["support_network", "Rede de apoio"],
    ],
  },
  {
    id: "life",
    title: "Vida acadêmica e profissional",
    description: "Contextos de estudo, trabalho e observações complementares.",
    fields: [
      ["academic_history", "Histórico acadêmico"],
      ["professional_history", "Histórico profissional"],
      ["observations", "Observações gerais"],
    ],
  },
] as const;

export function AnamnesisTab({ data, loading, saving, onSave }: AnamnesisTabProps) {
  const [openSection, setOpenSection] = useState<string>("initial");
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<AnamnesisWorkspace>>({});

  useEffect(() => {
    if (data) setDraft(data);
  }, [data]);

  const completedBySection = useMemo(() => {
    return Object.fromEntries(
      sections.map((section) => [
        section.id,
        section.fields.filter(([field]) => String(draft[field] ?? "").trim()).length,
      ]),
    );
  }, [draft]);

  if (loading) {
    return <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
      <section className="space-y-3">
        {sections.map((section) => {
          const open = openSection === section.id;
          const editing = editingSection === section.id;
          const completed = completedBySection[section.id] ?? 0;
          return (
            <article key={section.id} className="overflow-hidden rounded-xl border border-border bg-card">
              <button
                type="button"
                onClick={() => setOpenSection(open ? "" : section.id)}
                className="flex w-full items-center justify-between gap-4 px-4 py-4 text-left"
                aria-expanded={open}
              >
                <span>
                  <strong className="block text-xs text-foreground">{section.title}</strong>
                  <small className="mt-1 block text-[10px] text-muted-foreground">{section.description}</small>
                </span>
                <span className="flex shrink-0 items-center gap-3">
                  <small className="text-[10px] font-semibold text-primary">{completed}/{section.fields.length}</small>
                  <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-180")} />
                </span>
              </button>

              {open && (
                <div className="border-t border-border p-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    {section.fields.map(([field, label]) => (
                      <label key={field} className="space-y-1.5 text-[10px] font-semibold text-muted-foreground">
                        {label}
                        {editing ? (
                          <textarea
                            value={String(draft[field] ?? "")}
                            onChange={(event) => setDraft((current) => ({ ...current, [field]: event.target.value }))}
                            rows={4}
                            className="w-full resize-y rounded-md border border-border bg-background p-3 text-xs leading-5 text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
                          />
                        ) : (
                          <div className="min-h-24 whitespace-pre-wrap rounded-md bg-background/45 p-3 text-xs font-normal leading-5 text-muted-foreground">
                            {String(draft[field] ?? "").trim() || "Não informado."}
                          </div>
                        )}
                      </label>
                    ))}
                  </div>

                  <div className="mt-4 flex justify-end gap-2 border-t border-border pt-4">
                    {editing ? (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => { setDraft(data ?? {}); setEditingSection(null); }}>
                          Cancelar
                        </Button>
                        <Button
                          size="sm"
                          isLoading={saving}
                          leftIcon={<Save className="h-3.5 w-3.5" />}
                          onClick={async () => {
                            const payload = Object.fromEntries(section.fields.map(([field]) => [field, draft[field] ?? ""]));
                            await onSave(payload);
                            setEditingSection(null);
                          }}
                        >
                          Salvar seção
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" variant="outline" onClick={() => setEditingSection(section.id)}>
                        Editar seção
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </article>
          );
        })}
      </section>

      <aside className="space-y-3 lg:sticky lg:top-4 lg:self-start">
        <section className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-bold text-foreground">Preenchimento</h3>
            <strong className="text-sm text-primary">{data?.completion_percentage ?? 0}%</strong>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary">
            <span className="block h-full rounded-full bg-primary" style={{ width: `${data?.completion_percentage ?? 0}%` }} />
          </div>
          <p className="mt-3 text-[10px] leading-4 text-muted-foreground">
            A ficha pode ser concluída em etapas. Salve cada seção antes de continuar.
          </p>
        </section>

        <section className="rounded-xl border border-border bg-card p-4 text-[10px] text-muted-foreground">
          <div className="flex items-center gap-2 text-foreground">
            <History className="h-4 w-4 text-primary" />
            <strong>Histórico de versões</strong>
          </div>
          <p className="mt-3 leading-4">{data?.version_count ?? 0} versão(ões) preservada(s).</p>
          <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
            {data?.updated_at ? <CheckCircle2 className="h-3.5 w-3.5 text-primary" /> : <Clock3 className="h-3.5 w-3.5" />}
            <span>{data?.updated_at ? `Atualizada em ${new Date(data.updated_at).toLocaleString("pt-BR")}` : "Ainda não preenchida"}</span>
          </div>
        </section>
      </aside>
    </div>
  );
}
