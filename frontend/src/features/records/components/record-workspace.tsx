"use client";

import { useEffect, useState } from "react";
import {
  FileText,
  FolderOpen,
  History,
  Target,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { recordWorkspaceService } from "../services/record-workspace.service";
import {
  useClinicalAnamnesis,
  useClinicalDocuments,
  useClinicalEvolution,
  useClinicalEvolutions,
  useCreateClinicalEvolution,
  useDocumentMutations,
  useDuplicateClinicalEvolution,
  useFinalizeClinicalEvolution,
  useGoalMutations,
  useRecordSummary,
  useSaveClinicalAnamnesis,
  useTreatmentGoals,
  useUpdateClinicalEvolution,
} from "../hooks/use-record-workspace";
import type { EvolutionPayload, EvolutionWorkspace, RecordTab, TreatmentGoal } from "../types";
import { AnamnesisTab } from "./anamnesis-tab";
import { DocumentsTab } from "./documents-tab";
import { EvolutionEditor } from "./evolution-editor";
import { EvolutionTimeline } from "./evolution-timeline";
import { GoalsTab } from "./goals-tab";
import { PatientSelector } from "./patient-selector";
import { RecordHeader } from "./record-header";
import { RecordStats, RecordSupportPanel } from "./record-overview";

const tabs = [
  ["evolutions", "Histórico de evoluções", History],
  ["anamnesis", "Anamnese", FileText],
  ["goals", "Plano terapêutico", Target],
  ["documents", "Documentos", FolderOpen],
] as const;

export function RecordWorkspace({ patientId }: { patientId: number }) {
  const [activeTab, setActiveTab] = useState<RecordTab>("evolutions");
  const [patientDrawerOpen, setPatientDrawerOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingEvolution, setEditingEvolution] = useState<EvolutionWorkspace | null>(null);
  const [selectedEvolutionId, setSelectedEvolutionId] = useState<number | null>(null);
  const [exporting, setExporting] = useState(false);

  const summaryQuery = useRecordSummary(patientId);
  const evolutionsQuery = useClinicalEvolutions(patientId);
  const selectedEvolutionQuery = useClinicalEvolution(selectedEvolutionId);
  const anamnesisQuery = useClinicalAnamnesis(patientId);
  const goalsQuery = useTreatmentGoals(patientId);
  const documentsQuery = useClinicalDocuments(patientId);

  const createEvolution = useCreateClinicalEvolution(patientId);
  const updateEvolution = useUpdateClinicalEvolution(patientId, editingEvolution?.id);
  const finalizeEvolution = useFinalizeClinicalEvolution(patientId);
  const duplicateEvolution = useDuplicateClinicalEvolution(patientId);
  const saveAnamnesis = useSaveClinicalAnamnesis(patientId);
  const goalMutations = useGoalMutations(patientId);
  const documentMutations = useDocumentMutations(patientId);

  useEffect(() => {
    const first = evolutionsQuery.data?.results[0];
    if (!selectedEvolutionId && first) setSelectedEvolutionId(first.id);
  }, [evolutionsQuery.data?.results, selectedEvolutionId]);

  const openNewEvolution = () => {
    setEditingEvolution(null);
    setEditorOpen(true);
  };

  const editEvolution = (evolution: EvolutionWorkspace) => {
    setEditingEvolution(evolution);
    setEditorOpen(true);
  };

  const saveEvolution = async (payload: EvolutionPayload) => {
    if (editingEvolution) {
      const updated = await updateEvolution.mutateAsync(payload);
      setSelectedEvolutionId(updated.id);
    } else {
      const created = await createEvolution.mutateAsync(payload);
      setSelectedEvolutionId(created.id);
      setEditingEvolution(created);
    }
    setEditorOpen(false);
  };

  const finalize = async (id: number) => {
    await finalizeEvolution.mutateAsync(id);
    setEditorOpen(false);
  };

  const exportPdf = async () => {
    try {
      setExporting(true);
      await recordWorkspaceService.exportPatientPdf(patientId);
    } finally {
      setExporting(false);
    }
  };

  if (summaryQuery.isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-20 animate-pulse rounded-xl bg-secondary" />
        <div className="h-28 animate-pulse rounded-xl bg-secondary" />
        <div className="grid gap-3 xl:grid-cols-[18rem_1fr_18rem]">
          <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
          <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
          <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
        </div>
      </div>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-6 py-16 text-center">
        <h1 className="text-base font-bold text-foreground">Não foi possível carregar o prontuário</h1>
        <p className="mt-2 text-xs text-muted-foreground">Verifique sua permissão e tente novamente.</p>
        <Button className="mt-5" variant="outline" onClick={() => summaryQuery.refetch()}>Tentar novamente</Button>
      </div>
    );
  }

  const summary = summaryQuery.data;
  const evolutions = evolutionsQuery.data?.results ?? [];
  const selectedEvolution = selectedEvolutionQuery.data ?? evolutions.find((item) => item.id === selectedEvolutionId) ?? null;

  return (
    <div className="space-y-4">
      <RecordHeader
        summary={summary}
        exporting={exporting}
        onOpenPatients={() => setPatientDrawerOpen(true)}
        onNewEvolution={openNewEvolution}
        onOpenAnamnesis={() => setActiveTab("anamnesis")}
        onOpenDocuments={() => setActiveTab("documents")}
        onExport={exportPdf}
      />

      <RecordStats summary={summary} />

      <div className="grid items-start gap-4 xl:grid-cols-[18rem_minmax(0,1fr)] 2xl:grid-cols-[18rem_minmax(0,1fr)_18rem]">
        <PatientSelector
          selectedPatientId={patientId}
          mobileOpen={patientDrawerOpen}
          onMobileClose={() => setPatientDrawerOpen(false)}
        />

        <div className="min-w-0 space-y-4">
          <nav className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-card p-1" aria-label="Seções do prontuário">
            {tabs.map(([id, label, Icon]) => (
              <button
                key={id}
                type="button"
                onClick={() => setActiveTab(id)}
                className={`flex min-w-max flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-[11px] font-bold transition ${activeTab === id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}
                aria-current={activeTab === id ? "page" : undefined}
              >
                <Icon className="h-3.5 w-3.5" />{label}
              </button>
            ))}
          </nav>

          {activeTab === "evolutions" && (
            <EvolutionTimeline
              evolutions={evolutions}
              selected={selectedEvolution}
              loading={evolutionsQuery.isLoading || selectedEvolutionQuery.isLoading}
              onSelect={setSelectedEvolutionId}
              onEdit={editEvolution}
              onDuplicate={async (evolution) => {
                const date = window.prompt("Data da nova sessão (AAAA-MM-DD):", new Date().toISOString().slice(0, 10));
                if (!date) return;
                const created = await duplicateEvolution.mutateAsync({ id: evolution.id, sessionDate: date });
                setSelectedEvolutionId(created.id);
              }}
              onExport={exportPdf}
            />
          )}

          {activeTab === "anamnesis" && (
            <AnamnesisTab
              data={anamnesisQuery.data}
              loading={anamnesisQuery.isLoading}
              saving={saveAnamnesis.isPending}
              onSave={(payload) => saveAnamnesis.mutateAsync(payload).then(() => undefined)}
            />
          )}

          {activeTab === "goals" && (
            <GoalsTab
              goals={goalsQuery.data ?? []}
              loading={goalsQuery.isLoading}
              creating={goalMutations.create.isPending}
              updating={goalMutations.update.isPending}
              onCreate={(payload) => goalMutations.create.mutateAsync(payload).then(() => undefined)}
              onUpdate={(id, payload) => goalMutations.update.mutateAsync({ id, payload }).then(() => undefined)}
              onArchive={(id) => goalMutations.archive.mutateAsync(id).then(() => undefined)}
            />
          )}

          {activeTab === "documents" && (
            <DocumentsTab
              patientId={patientId}
              documents={documentsQuery.data ?? []}
              loading={documentsQuery.isLoading}
              uploading={documentMutations.upload.isPending}
              onUpload={(data) => documentMutations.upload.mutateAsync(data).then(() => undefined)}
              onArchive={(id) => documentMutations.archive.mutateAsync(id).then(() => undefined)}
            />
          )}
        </div>

        <div className="hidden 2xl:block">
          <RecordSupportPanel
            summary={summary}
            onOpenGoal={() => setActiveTab("goals")}
            onOpenDocuments={() => setActiveTab("documents")}
          />
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 py-2 text-[10px] text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-primary" />
        Dados clínicos protegidos por controle de acesso, auditoria e criptografia em repouso.
      </div>

      <EvolutionEditor
        patientId={patientId}
        open={editorOpen}
        evolution={editingEvolution}
        saving={createEvolution.isPending || updateEvolution.isPending}
        finalizing={finalizeEvolution.isPending}
        onClose={() => setEditorOpen(false)}
        onSave={saveEvolution}
        onFinalize={finalize}
      />
    </div>
  );
}
