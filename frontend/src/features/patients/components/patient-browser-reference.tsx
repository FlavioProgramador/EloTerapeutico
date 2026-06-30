"use client";

import { useRouter } from "next/navigation";

import { useAuth } from "@/contexts/auth";
import { usePatientReferenceData } from "../hooks/use-patient-reference-data";
import { usePatientReferenceFilters } from "../hooks/use-patient-reference-filters";
import { countPatientFilters } from "./patient-list-config";
import type { PatientListItem } from "./patient-list-item";
import { PatientListEmpty, PatientListError } from "./patient-list-state";
import { PatientMetricsReference } from "./patient-metrics-reference";
import { PatientPageHeader } from "./patient-page-header";
import { PatientTable, PatientTableSkeleton } from "./patient-table";
import { PatientToolbarReference } from "./patient-toolbar-reference";

export function PatientBrowserReference() {
  const router = useRouter();
  const { user } = useAuth();
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
  const goToNew = () => router.push("/dashboard/patients/new");
  const clearAll = () => {
    state.setSearch("");
    state.clearFilters();
  };
  const filtered = Boolean(state.debouncedSearch || filterCount);

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
          canAccessRecords={canManage}
          onReminderChange={(patient, enabled) =>
            data.reminder.mutate({ id: patient.id, enabled })
          }
          onArchive={data.archivePatient}
          onRestore={(patient) => data.restore.mutate(patient.id)}
          onPageChange={state.setPage}
          onPageSizeChange={(size) => {
            state.setPageSize(size);
            state.setPage(1);
          }}
        />
      )}
    </div>
  );
}
