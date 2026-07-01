"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { recordWorkspaceService } from "../services/record-workspace.service";
import {
  useClinicalDocuments,
  useClinicalEvolution,
  useClinicalEvolutions,
  useCreateClinicalEvolution,
  useDocumentMutations,
  useDuplicateClinicalEvolution,
  useFinalizeClinicalEvolution,
  useRecordSummary,
  useUpdateClinicalEvolution,
} from "../hooks/use-record-workspace";
import type {
  EvolutionPayload,
  EvolutionWorkspace,
  RecordTab,
} from "../types";

import { AppointmentsTab } from "./appointments-tab";
import { FormsTab } from "./forms-tab";
import { ExportsTab } from "./exports-tab";
import { DocumentsTab } from "./documents-tab";
import { EvolutionEditor } from "./evolution-editor";
import { EvolutionTimeline } from "./evolution-timeline";
import { PatientSelector } from "./patient-selector";
import { RecordHeader } from "./record-header";
import { RecordStats } from "./record-overview";
import { RecordTabsNav } from "./record-tabs-nav";

function isRecordTab(value: string | null): value is RecordTab {
  return ["evolutions", "appointments", "documents", "forms", "exports"].includes(
    value ?? "",
  );
}

export function RecordWorkspace({ patientId }: { patientId: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState<RecordTab>(
    isRecordTab(requestedTab) ? requestedTab : "evolutions",
  );
  const [patientDrawerOpen, setPatientDrawerOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingEvolution, setEditingEvolution] =
    useState<EvolutionWorkspace | null>(null);
  const [selectedEvolutionId, setSelectedEvolutionId] = useState<number | null>(
    null,
  );
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (isRecordTab(requestedTab) && requestedTab !== activeTab) {
      setActiveTab(requestedTab);
    }
  }, [activeTab, requestedTab]);

  const changeTab = (tab: RecordTab) => {
    setActiveTab(tab);
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const summaryQuery = useRecordSummary(patientId);
  const evolutionsQuery = useClinicalEvolutions(
    patientId,
    1,
    undefined,
    activeTab === "evolutions",
  );
  const selectedEvolutionQuery = useClinicalEvolution(
    activeTab === "evolutions" ? selectedEvolutionId : null,
  );
  const documentsQuery = useClinicalDocuments(
    patientId,
    activeTab === "documents",
  );

  const createEvolution = useCreateClinicalEvolution(patientId);
  const updateEvolution = useUpdateClinicalEvolution(
    patientId,
    editingEvolution?.id,
  );
  const finalizeEvolution = useFinalizeClinicalEvolution(patientId);
  const duplicateEvolution = useDuplicateClinicalEvolution(patientId);
  const documentMutations = useDocumentMutations(patientId);

  useEffect(() => {
    if (activeTab !== "evolutions") return;
    const first = evolutionsQuery.data?.results[0];
    const selectedStillVisible = evolutionsQuery.data?.results.some(
      (item) => item.id === selectedEvolutionId,
    );
    if ((!selectedEvolutionId || !selectedStillVisible) && first) {
      setSelectedEvolutionId(first.id);
    }
  }, [activeTab, evolutionsQuery.data?.results, selectedEvolutionId]);

  const openNewEvolution = (appointmentId?: number) => {
    if (appointmentId) {
      setEditingEvolution({ appointment: appointmentId } as any);
    } else {
      setEditingEvolution(null);
    }
    changeTab("evolutions");
    setEditorOpen(true);
  };

  const editEvolution = (evolution: EvolutionWorkspace) => {
    setEditingEvolution(evolution);
    setEditorOpen(true);
  };

  const saveEvolution = async (payload: EvolutionPayload) => {
    if (editingEvolution && editingEvolution.id) {
      const updated = await updateEvolution.mutateAsync(payload);
      setSelectedEvolutionId(updated.id);
    } else {
      // Repassa o ID de consulta preenchido anteriormente no estado, se existir
      const finalPayload = {
        ...payload,
        appointment: editingEvolution?.appointment || payload.appointment,
      };
      const created = await createEvolution.mutateAsync(finalPayload);
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
        <div className="grid gap-3 xl:grid-cols-[18rem_1fr]">
          <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
          <div className="h-[36rem] animate-pulse rounded-xl bg-secondary" />
        </div>
      </div>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-6 py-16 text-center">
        <h1 className="text-base font-bold text-foreground">
          Não foi possível carregar o prontuário
        </h1>
        <p className="mt-2 text-xs text-muted-foreground">
          Verifique sua permissão e tente novamente.
        </p>
        <Button
          className="mt-5"
          variant="outline"
          onClick={() => summaryQuery.refetch()}
        >
          Tentar novamente
        </Button>
      </div>
    );
  }

  const summary = summaryQuery.data;
  const evolutions = evolutionsQuery.data?.results ?? [];
  const selectedEvolution =
    selectedEvolutionQuery.data ??
    evolutions.find((item) => item.id === selectedEvolutionId) ??
    null;

  return (
    <div className="space-y-4">
      <RecordHeader
        summary={summary}
        exporting={exporting}
        onBack={() => router.push("/dashboard/patients")}
        onNewEvolution={() => openNewEvolution()}
        onFillForm={() => changeTab("forms")}
        onExport={exportPdf}
      />

      <RecordStats summary={summary} />

      <div className="grid items-start gap-4 xl:grid-cols-[18rem_minmax(0,1fr)]">
        <PatientSelector
          selectedPatientId={patientId}
          mobileOpen={patientDrawerOpen}
          onMobileClose={() => setPatientDrawerOpen(false)}
        />

        <div className="min-w-0 space-y-4">
          <RecordTabsNav activeTab={activeTab} onChange={changeTab} />

          {activeTab === "appointments" && (
            <AppointmentsTab
              patientId={patientId}
              onNewEvolution={openNewEvolution}
              onViewEvolution={(evoId) => {
                setSelectedEvolutionId(evoId);
                changeTab("evolutions");
              }}
            />
          )}

          {activeTab === "evolutions" && (
            <EvolutionTimeline
              evolutions={evolutions}
              selected={selectedEvolution}
              loading={
                evolutionsQuery.isLoading || selectedEvolutionQuery.isLoading
              }
              onSelect={setSelectedEvolutionId}
              onEdit={editEvolution}
              onDuplicate={async (evolution) => {
                const date = window.prompt(
                  "Data da nova sessão (AAAA-MM-DD):",
                  new Date().toISOString().slice(0, 10),
                );
                if (!date) return;
                const created = await duplicateEvolution.mutateAsync({
                  id: evolution.id,
                  sessionDate: date,
                });
                setSelectedEvolutionId(created.id);
              }}
              onExport={exportPdf}
            />
          )}

          {activeTab === "documents" && (
            <DocumentsTab
              patientId={patientId}
              documents={documentsQuery.data ?? []}
              loading={documentsQuery.isLoading}
              uploading={documentMutations.upload.isPending}
              updating={documentMutations.update.isPending}
              onUpload={(data) =>
                documentMutations.upload.mutateAsync(data).then(() => undefined)
              }
              onUpdate={(id, payload) =>
                documentMutations.update
                  .mutateAsync({ id, payload })
                  .then(() => undefined)
              }
              onArchive={(id) =>
                documentMutations.archive.mutateAsync(id).then(() => undefined)
              }
            />
          )}

          {activeTab === "forms" && (
            <FormsTab patientId={patientId} />
          )}

          {activeTab === "exports" && (
            <ExportsTab patientId={patientId} />
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 py-2 text-[10px] text-muted-foreground">
        <span className="h-2 w-2 rounded-full bg-emerald-400" />
        Dados clínicos protegidos por controle de acesso, auditoria e criptografia
        em repouso.
      </div>

      <EvolutionEditor
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
