"use client";

import { useState } from "react";
import { toast } from "sonner";

import { useAuth } from "@/contexts/auth";
import { usePatientReferenceData } from "../hooks/use-patient-reference-data";
import { usePatientReferenceFilters } from "../hooks/use-patient-reference-filters";
import { patientsService } from "../services/patients.service";
import { NewPatientModal } from "./new-patient-modal";
import { countPatientFilters } from "./patient-list-config";
import type { PatientListItem } from "./patient-list-item";
import { PatientListEmpty, PatientListError } from "./patient-list-state";
import { PatientMetricsReference } from "./patient-metrics-reference";
import { PatientPageHeader } from "./patient-page-header";
import { PatientTable, PatientTableSkeleton } from "./patient-table";
import { PatientToolbarReference } from "./patient-toolbar-reference";

export function PatientBrowserReference() {
  const { user } = useAuth();
  const [drawer, setDrawer] = useState<{
    open: boolean;
    patientId?: number;
  }>({ open: false });
  const state = usePatientReferenceFilters();
  const data = usePatientReferenceData({
    params: state.params,
    search: state.debouncedSearch,
    filters: state.filters,
    birthdaysOnly: state.birthdaysOnly,
    pageSize: state.pageSize,
  });

  const patients = (data.list.data?.results ?? []) as PatientListItem[];
  const filterCount = countPatientFilters(state.filters, state.birthdaysOnly);
  const canManage = (patient: PatientListItem) =>
    user?.role === "admin" ||
    (user?.role === "therapist" && patient.therapist === user.id);
  const canAccessRecords = (patient: PatientListItem) =>
    user?.role === "admin" ||
    (user?.role === "therapist" && patient.therapist === user.id);
  const goToNew = () => setDrawer({ open: true });
  const clearAll = () => {
    state.setSearch("");
    state.clearFilters();
  };
  const filtered = Boolean(state.debouncedSearch || filterCount);

  const createRegistrationLink = async (patient: PatientListItem) => {
    try {
      const result = await patientsService.createRegistrationLink(patient.id);
      const url = new URL(result.path, window.location.origin).toString();
      await navigator.clipboard.writeText(url);
      toast.success("Link seguro copiado para a área de transferência.");
    } catch {
      toast.error("Não foi possível gerar o link de cadastro.");
    }
  };

  return (
    <div className="space-y-5">
      <PatientPageHeader onNew={goToNew} />

      <PatientMetricsReference
        total={data.metrics.data?.total ?? 0}
        active={data.metrics.data?.active ?? 0}
        birthdays={data.birthdayCount.data ?? 0}
        loading={data.metrics.isLoading || data.birthdayCount.isLoading}
      />

      <PatientToolbarReference
        search={state.search}
        filters={state.filters}
        draftFilters={state.draftFilters}
        userRole={user?.role}
        filtersOpen={state.filtersOpen}
        birthdaysOnly={state.birthdaysOnly}
        filterCount={filterCount}
        exporting={data.exporting}
        onSearchChange={state.setSearch}
        onDraftFiltersChange={state.setDraftFilters}
        onToggleFilters={() => state.setFiltersOpen((value) => !value)}
        onToggleBirthdays={() => {
          state.setBirthdaysOnly((value) => !value);
          state.setPage(1);
        }}
        onApplyFilters={() => {
          state.setFilters(state.draftFilters);
          state.setPage(1);
          state.setFiltersOpen(false);
        }}
        onClearFilters={state.clearFilters}
        onExport={data.exportCsv}
      />

      {data.list.isLoading && !data.list.data ? (
        <PatientTableSkeleton />
      ) : data.list.isError ? (
        <PatientListError onRetry={() => data.list.refetch()} />
      ) : patients.length === 0 ? (
        <PatientListEmpty
          onAction={filtered ? clearAll : goToNew}
          label={filtered ? "Limpar pesquisa e filtros" : "Novo paciente"}
          isFiltered={filtered}
        />
      ) : (
        <PatientTable
          patients={patients}
          pagination={data.list.data?.pagination}
          page={state.page}
          pageSize={state.pageSize}
          loading={data.list.isFetching}
          reminderPendingId={data.reminder.variables?.id}
          canManage={canManage}
          canAccessRecords={canAccessRecords}
          onReminderChange={(patient, enabled) =>
            data.reminder.mutate({ id: patient.id, enabled })
          }
          onEdit={(patient) =>
            setDrawer({ open: true, patientId: patient.id })
          }
          onDeactivate={data.deactivatePatient}
          onRestore={(patient) => {
            if (window.confirm(`Reativar ${patient.display_name}?`)) {
              data.restore.mutate(patient.id);
            }
          }}
          onRemove={data.archivePatient}
          onRegistrationLink={createRegistrationLink}
          onPageChange={state.setPage}
          onPageSizeChange={(size) => {
            state.setPageSize(size);
            state.setPage(1);
          }}
        />
      )}

      <NewPatientModal
        open={drawer.open}
        patientId={drawer.patientId}
        onClose={() => setDrawer({ open: false })}
        onSaved={() => data.refresh()}
      />
    </div>
  );
}
