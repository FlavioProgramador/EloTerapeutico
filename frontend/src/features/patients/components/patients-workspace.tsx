"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { NewPatientModal } from "./new-patient-modal";
import { PatientDetailPanel } from "./patient-detail-panel";
import { PatientImportModal } from "./patient-import-modal";
import { PatientListPanel } from "./patient-list-panel";
import { PatientMetricsGrid } from "./patient-metrics";
import { PatientToolbar } from "./patient-toolbar";
import {
  exportPatientsCsv,
  usePatientDashboardList,
  usePatientMetrics,
  usePatientPanel,
} from "../hooks/use-patient-dashboard";
import { usePatientWorkspaceState } from "../hooks/use-patient-workspace";

export function PatientsWorkspace() {
  const state = usePatientWorkspaceState();
  const [newOpen, setNewOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const listQuery = usePatientDashboardList(state.queryFilters);
  const metricsQuery = usePatientMetrics();
  const panelQuery = usePatientPanel(state.selectedId);
  const patients = listQuery.data?.results ?? [];
  const { selectedId, setSelectedId } = state;

  useEffect(() => {
    if (!selectedId && patients[0]) {
      setSelectedId(patients[0].id);
    }
  }, [patients, selectedId, setSelectedId]);

  const handleExport = async () => {
    try {
      setExporting(true);
      const blob = await exportPatientsCsv(state.queryFilters);
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
  };

  if (listQuery.isError) {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-10 text-center">
        <h1 className="text-base font-bold text-foreground">
          Não foi possível carregar os pacientes
        </h1>
        <p className="mt-2 text-xs text-muted-foreground">
          Verifique sua conexão ou suas permissões e tente novamente.
        </p>
        <button
          type="button"
          onClick={() => listQuery.refetch()}
          className="mt-4 rounded-md border border-border px-4 py-2 text-xs font-semibold text-foreground hover:bg-secondary"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <PatientToolbar
        filters={state.filters}
        advancedOpen={state.advancedOpen}
        exporting={exporting}
        onFiltersChange={state.setFilters}
        onAdvancedToggle={state.toggleAdvanced}
        onNew={() => setNewOpen(true)}
        onImport={() => setImportOpen(true)}
        onExport={handleExport}
      />

      <PatientMetricsGrid metrics={metricsQuery.data} />

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.85fr)_minmax(20rem,1fr)]">
        <PatientListPanel
          patients={patients}
          selectedId={selectedId}
          loading={listQuery.isLoading}
          total={listQuery.data?.count ?? 0}
          page={state.page}
          pageSize={6}
          onSelect={setSelectedId}
          onPageChange={state.setPage}
        />
        <PatientDetailPanel
          data={panelQuery.data}
          loading={panelQuery.isLoading}
          onClose={selectedId ? () => setSelectedId(undefined) : undefined}
        />
      </div>

      <NewPatientModal
        open={newOpen}
        onClose={() => setNewOpen(false)}
        onCreated={setSelectedId}
      />
      <PatientImportModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
      />
    </div>
  );
}
