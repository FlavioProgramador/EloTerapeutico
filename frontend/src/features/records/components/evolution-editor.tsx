"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Save } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import type { EvolutionPayload, EvolutionWorkspace } from "../types";

interface EvolutionEditorProps {
  patientId: number;
  open: boolean;
  evolution?: EvolutionWorkspace | null;
  saving: boolean;
  finalizing: boolean;
  onClose: () => void;
  onSave: (payload: EvolutionPayload) => Promise<void>;
  onFinalize: (id: number) => Promise<void>;
}

const emptyForm: EvolutionPayload = {
  session_date: new Date().toISOString().slice(0, 10),
  session_time: "",
  duration_minutes: 50,
  modality: "in_person",
  appointment_type: "individual",
  emotional_state: "",
  chief_complaint: "",
  patient_report: "",
  therapist_observations: "",
  interventions: "",
  perceived_evolution: "",
  homework: "",
  referrals: "",
  next_steps: "",
  cid10: "",
};

const sections = [
  {
    title: "Contexto da sessão",
    fields: [
      ["emotional_state", "Estado emocional observado"],
      ["chief_complaint", "Queixa principal"],
      ["patient_report", "Relato do paciente"],
    ],
  },
  {
    title: "Registro do terapeuta",
    fields: [
      ["therapist_observations", "Observações clínicas"],
      ["interventions", "Técnicas e intervenções utilizadas"],
      ["perceived_evolution", "Evolução percebida"],
    ],
  },
  {
    title: "Continuidade do cuidado",
    fields: [
      ["homework", "Tarefas ou orientações"],
      ["referrals", "Encaminhamentos"],
      ["next_steps", "Próximos passos"],
    ],
  },
] as const;

export function EvolutionEditor({
  patientId,
  open,
  evolution,
  saving,
  finalizing,
  onClose,
  onSave,
  onFinalize,
}: EvolutionEditorProps) {
  const storageKey = useMemo(
    () => `elo:record-draft:${patientId}:${evolution?.id ?? "new"}`,
    [patientId, evolution?.id],
  );
  const [form, setForm] = useState<EvolutionPayload>(emptyForm);
  const [dirty, setDirty] = useState(false);
  const [recovered, setRecovered] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!open) return;
    if (evolution) {
      setForm({
        session_date: evolution.session_date,
        session_time: evolution.session_time ?? "",
        duration_minutes: evolution.duration_minutes,
        modality: evolution.modality,
        appointment_type: evolution.appointment_type,
        emotional_state: evolution.emotional_state,
        chief_complaint: evolution.chief_complaint,
        patient_report: evolution.patient_report,
        therapist_observations: evolution.therapist_observations || evolution.content,
        interventions: evolution.interventions,
        perceived_evolution: evolution.perceived_evolution,
        homework: evolution.homework,
        referrals: evolution.referrals,
        next_steps: evolution.next_steps,
        cid10: evolution.cid10 ?? "",
      });
      setRecovered(false);
    } else {
      const localDraft = window.localStorage.getItem(storageKey);
      if (localDraft) {
        try {
          setForm({ ...emptyForm, ...(JSON.parse(localDraft) as EvolutionPayload) });
          setRecovered(true);
        } catch {
          setForm(emptyForm);
        }
      } else {
        setForm(emptyForm);
        setRecovered(false);
      }
    }
    setDirty(false);
  }, [open, evolution, storageKey]);

  useEffect(() => {
    if (!open || !dirty) return;
    const timeout = window.setTimeout(() => {
      window.localStorage.setItem(storageKey, JSON.stringify(form));
      setLastSavedAt(new Date());
    }, 700);
    return () => window.clearTimeout(timeout);
  }, [dirty, form, open, storageKey]);

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [dirty]);

  const change = <K extends keyof EvolutionPayload>(field: K, value: EvolutionPayload[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
    setDirty(true);
  };

  const closeSafely = () => {
    if (dirty && !window.confirm("Há alterações não enviadas. Deseja fechar mesmo assim?")) return;
    onClose();
  };

  const save = async () => {
    if (!form.session_date || !form.therapist_observations?.trim()) return;
    await onSave(form);
    window.localStorage.removeItem(storageKey);
    setDirty(false);
    setRecovered(false);
    setLastSavedAt(new Date());
  };

  const finalize = async () => {
    if (!evolution) return;
    if (!window.confirm("Finalizar esta evolução? Depois disso, alterações deverão ser registradas por histórico auditável ou aditivo.")) return;
    if (dirty) await save();
    await onFinalize(evolution.id);
    window.localStorage.removeItem(storageKey);
  };

  return (
    <Modal
      isOpen={open}
      onClose={closeSafely}
      title={evolution ? "Editar evolução clínica" : "Nova evolução clínica"}
      description="Organize o registro em blocos curtos. O conteúdo local é recuperado se o navegador for fechado acidentalmente."
      className="max-w-4xl"
    >
      <div className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-secondary/40 px-3 py-2 text-[10px]">
          <span className="inline-flex items-center gap-2 text-muted-foreground">
            {dirty ? <AlertCircle className="h-3.5 w-3.5 text-amber-400" /> : <CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
            {dirty ? "Alterações aguardando envio" : "Rascunho sincronizado"}
          </span>
          <span className="text-muted-foreground">
            {recovered
              ? "Rascunho local recuperado"
              : lastSavedAt
                ? `Salvo localmente às ${lastSavedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`
                : "Recuperação automática ativa"}
          </span>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Data
            <input type="date" value={form.session_date} onChange={(event) => change("session_date", event.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Horário
            <input type="time" value={form.session_time ?? ""} onChange={(event) => change("session_time", event.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Duração
            <input type="number" min={1} max={600} value={form.duration_minutes ?? 50} onChange={(event) => change("duration_minutes", Number(event.target.value))} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground" />
          </label>
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Modalidade
            <select value={form.modality} onChange={(event) => change("modality", event.target.value as EvolutionPayload["modality"])} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground">
              <option value="in_person">Presencial</option><option value="online">Online</option><option value="hybrid">Híbrido</option>
            </select>
          </label>
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Atendimento
            <select value={form.appointment_type} onChange={(event) => change("appointment_type", event.target.value as EvolutionPayload["appointment_type"])} className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground">
              <option value="individual">Individual</option><option value="couple">Casal</option><option value="family">Familiar</option><option value="group">Grupo</option><option value="other">Outro</option>
            </select>
          </label>
        </div>

        {sections.map((section) => (
          <fieldset key={section.title} className="rounded-xl border border-border p-4">
            <legend className="px-2 text-xs font-bold text-foreground">{section.title}</legend>
            <div className="grid gap-4 md:grid-cols-2">
              {section.fields.map(([field, label], index) => (
                <label key={field} className={`space-y-1 text-[10px] font-semibold text-muted-foreground ${index === 2 ? "md:col-span-2" : ""}`}>
                  {label}
                  <textarea value={String(form[field] ?? "")} onChange={(event) => change(field, event.target.value)} rows={index === 2 ? 4 : 3} className="w-full resize-y rounded-md border border-border bg-background p-3 text-xs leading-5 text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15" />
                </label>
              ))}
            </div>
          </fieldset>
        ))}

        <div className="flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-end">
          <Button variant="ghost" onClick={closeSafely}>Cancelar</Button>
          <Button variant="outline" isLoading={saving} onClick={save} disabled={!form.therapist_observations?.trim()} leftIcon={<Save className="h-4 w-4" />}>
            Salvar rascunho
          </Button>
          {evolution && evolution.status === "draft" && (
            <Button isLoading={finalizing} onClick={finalize} disabled={!form.therapist_observations?.trim()}>
              Finalizar evolução
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
