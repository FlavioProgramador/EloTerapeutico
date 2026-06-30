"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { useAuth } from "@/contexts/auth";
import { NewPatientModal } from "./new-patient-modal";
import { PatientImportModal } from "./patient-import-modal";
import { PatientListPanel } from "./patient-list-panel";
import { PatientMetricsGrid } from "./patient-metrics";
import { PatientSidePanel } from "./patient-side-panel";
import { PatientToolbarSafe } from "./patient-toolbar-safe";
import {
  downloadPatientCsv,
  usePatientPage,
  usePatientPageMetrics,
  usePatientPagePanel,
} from "../hooks/use-patient-page";
import { usePatientWorkspaceState } from "../hooks/use-patient-workspace";

export function PatientsPageContent() {
  const { user } = useAuth();
  const state = usePatientWorkspaceState();
  const [newOpen, setNewOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const list = usePatientPage(state.queryFilters);
  const metrics = usePatientPageMetrics();
  const panel = usePatientPagePanel(state.selectedId);
  const patients = list.data?.results ?? [];

  useEffect(() => {
    if (!state.selectedId && patients[0]) state.setSelectedId(patients[0].id);
  }, [patients, state]);

  async function exportCsv() {
    try {
      setExporting(true);
      const blob = await downloadPatientCsv(state.queryFilters);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "pacientes.csv";
      link.click();
      URL.revokeObjectURL(url);
      toast.success("Exportação concluída.");
    } catch {
      toast.error("Não foi possível exportar os pacientes.");
    } finally {
      setExporting(false);
    }
  }

  if (list.isError) {
    return (
      <div className="rounded-xl border border-destructive/30 p-10 text-center">
        <p className="text-sm font-semibold">Não foi possível carregar os pacientes.</p>
        <button type="button" onClick={() => list.refetch()} className="mt-4 rounded-md border px-4 py-2 text-xs">
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PatientToolbarSafe
        filters={state.filters}
        advancedOpen={state.advancedOpen}
        exporting={exporting}
        canImport={user?.role === "therapist"}
        onChange={state.setFilters}
        onAdvanced={state.toggleAdvanced}
        onNew={() => setNewOpen(true)}
        onImport={() => setImportOpen(true)}
        onExport={exportCsv}
      />
      <PatientMetricsGrid metrics={metrics.data} />
      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.85fr)_minmax(20rem,1fr)]">
        <PatientListPanel
          patients={patients}
          selectedId={state.selectedId}
          loading={list.isLoading}
          total={list.data?.pagination.count ?? 0}
          page={state.page}
          pageSize={6}
          onSelect={state.setSelectedId}
          onPageChange={state.setPage}
        />
        <PatientSidePanel
          data={panel.data}
          loading={panel.isLoading}
          onClose={state.selectedId ? () => state.setSelectedId(undefined) : undefined}
        />
      </div>
      <NewPatientModal open={newOpen} onClose={() => setNewOpen(false)} onCreated={state.setSelectedId} />
      {user?.role === "therapist" && (
        <PatientImportModal open={importOpen} onClose={() => setImportOpen(false)} />
      )}
    </div>
  );
}
