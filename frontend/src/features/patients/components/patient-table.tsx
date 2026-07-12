import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { PatientPageData } from "./patient-list-config";
import type { PatientListItem } from "./patient-list-item";
import { PatientDesktopRow, PatientMobileCard } from "./patient-table-row";

interface Props {
  patients: PatientListItem[];
  pagination?: PatientPageData["pagination"];
  page: number;
  pageSize: number;
  loading: boolean;
  reminderPendingId?: number;
  canManage: (patient: PatientListItem) => boolean;
  canAccessRecords: (patient: PatientListItem) => boolean;
  onReminderChange: (patient: PatientListItem, enabled: boolean) => void;
  onEdit: (patient: PatientListItem) => void;
  onDeactivate: (patient: PatientListItem) => void;
  onRestore: (patient: PatientListItem) => void;
  onRemove: (patient: PatientListItem) => void;
  onRegistrationLink: (patient: PatientListItem) => void;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

export function PatientTableSkeleton() {
  return (
    <section
      className="overflow-hidden rounded-xl border border-border bg-card"
      aria-busy="true"
      aria-label="Carregando pacientes"
    >
      {Array.from({ length: 7 }).map((_, index) => (
        <div
          key={index}
          className="grid grid-cols-[1.5fr_1.3fr_.7fr_1fr_.6fr_.7fr_3rem] gap-4 border-b border-border/70 p-4 last:border-0"
        >
          {Array.from({ length: 7 }).map((__, cell) => (
            <div key={cell} className="h-8 animate-pulse rounded bg-secondary" />
          ))}
        </div>
      ))}
    </section>
  );
}

export function PatientTable({
  patients,
  pagination,
  page,
  pageSize,
  loading,
  reminderPendingId,
  canManage,
  canAccessRecords,
  onReminderChange,
  onEdit,
  onDeactivate,
  onRestore,
  onRemove,
  onRegistrationLink,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const start = pagination?.count
    ? (pagination.current_page - 1) * pageSize + 1
    : 0;
  const end = pagination?.count
    ? Math.min(start + patients.length - 1, pagination.count)
    : 0;

  const rowProps = (patient: PatientListItem) => ({
    patient,
    canManage: canManage(patient),
    canAccessRecords: canAccessRecords(patient),
    reminderPending: reminderPendingId === patient.id,
    onReminderChange: (enabled: boolean) => onReminderChange(patient, enabled),
    onEdit: () => onEdit(patient),
    onDeactivate: () => onDeactivate(patient),
    onRestore: () => onRestore(patient),
    onRemove: () => onRemove(patient),
    onRegistrationLink: () => onRegistrationLink(patient),
  });

  return (
    <section className="overflow-visible rounded-xl border border-border bg-card">
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[980px] border-collapse text-left">
          <thead className="border-b border-border bg-secondary/30 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              {[
                "Paciente",
                "Contato",
                "Idade",
                "Convênio / pagador",
                "Lembrete",
                "Status",
                "",
              ].map((label) => (
                <th
                  key={label || "actions"}
                  className="px-3 py-3 font-semibold first:pl-4"
                >
                  {label || <span className="sr-only">Ações</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/70">
            {patients.map((patient) => (
              <PatientDesktopRow key={patient.id} {...rowProps(patient)} />
            ))}
          </tbody>
        </table>
      </div>

      <div className="divide-y divide-border md:hidden">
        {patients.map((patient) => (
          <PatientMobileCard key={patient.id} {...rowProps(patient)} />
        ))}
      </div>

      <footer className="flex flex-col gap-3 border-t border-border bg-secondary/15 px-4 py-3 text-sm text-muted-foreground lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="patients-page-size">Mostrar</label>
          <select
            id="patients-page-size"
            value={pageSize}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            className="h-9 rounded-md border border-border bg-background px-2 text-sm text-foreground"
          >
            {[10, 25, 50].map((size) => (
              <option key={size}>{size}</option>
            ))}
          </select>
          <span>por página</span>
          <span className="hidden sm:inline">
            Mostrando {start}–{end} de {pagination?.count ?? 0}
          </span>
        </div>
        <div className="flex items-center justify-between gap-2 sm:justify-end">
          <Button
            size="icon"
            variant="outline"
            className="h-9 w-9"
            disabled={!pagination?.previous || loading}
            onClick={() => onPageChange(Math.max(1, page - 1))}
            aria-label="Página anterior"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="min-w-24 text-center">
            Página {pagination?.current_page ?? page} de {pagination?.total_pages ?? 1}
          </span>
          <Button
            size="icon"
            variant="outline"
            className="h-9 w-9"
            disabled={!pagination?.next || loading}
            onClick={() => onPageChange(page + 1)}
            aria-label="Próxima página"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </footer>
    </section>
  );
}
