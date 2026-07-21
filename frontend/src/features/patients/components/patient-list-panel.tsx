import { ChevronLeft, ChevronRight, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { maskEmail, maskPhone } from "@/lib/privacy/masks";
import type { PatientDashboardItem } from "../types";

interface Props {
  patients: PatientDashboardItem[];
  selectedId?: number;
  loading: boolean;
  total: number;
  page: number;
  pageSize: number;
  onSelect: (id: number) => void;
  onPageChange: (page: number) => void;
}

const statusVariant = {
  active: "success",
  evaluation: "warning",
  waiting_return: "outline",
  discharged: "primary",
  inactive: "muted",
  archived: "muted",
} as const;

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function formatSession(value?: string | null) {
  if (!value) return "Não agendado";
  const date = new Date(value);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function PatientTags({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-1">
      {tags.slice(0, 2).map((tag) => (
        <span
          key={tag}
          className="rounded-md bg-primary/8 px-2 py-1 text-xs text-primary"
        >
          {tag}
        </span>
      ))}
      {tags.length > 2 && (
        <span className="rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
          +{tags.length - 2}
        </span>
      )}
    </div>
  );
}

export function PatientListPanel({
  patients,
  selectedId,
  loading,
  total,
  page,
  pageSize,
  onSelect,
  onPageChange,
}: Props) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (loading) {
    return (
      <div
        role="status"
        aria-busy="true"
        aria-label="Carregando lista de pacientes"
        className="space-y-2 rounded-xl border border-border bg-card p-3"
      >
        {Array.from({ length: pageSize }).map((_, index) => (
          <div
            key={index}
            className="h-24 animate-pulse rounded-lg bg-secondary"
          />
        ))}
      </div>
    );
  }

  if (!patients.length) {
    return (
      <div className="grid min-h-72 place-items-center rounded-xl border border-dashed border-border bg-card p-8 text-center">
        <EmptyState
          icon={<Search className="h-6 w-6 text-muted-foreground" />}
          title="Nenhum paciente encontrado"
          description="Ajuste a busca ou remova os filtros ativos."
        />
      </div>
    );
  }

  return (
    <section className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <thead className="border-b border-border bg-secondary/35 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Paciente</th>
              <th className="px-3 py-3">Contato</th>
              <th className="px-3 py-3">Última sessão</th>
              <th className="px-3 py-3">Próxima sessão</th>
              <th className="px-3 py-3">Status</th>
              <th className="px-3 py-3">Etiquetas</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/70">
            {patients.map((patient) => {
              const selected = patient.id === selectedId;
              return (
                <tr
                  key={patient.id}
                  tabIndex={0}
                  role="button"
                  aria-selected={selected}
                  aria-label={`Selecionar paciente ${patient.display_name}`}
                  onClick={() => onSelect(patient.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(patient.id);
                    }
                  }}
                  className={`cursor-pointer outline-none transition-colors focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary ${
                    selected
                      ? "bg-primary/8 shadow-[inset_3px_0_0_hsl(var(--primary))]"
                      : "hover:bg-secondary/45"
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <span
                        aria-hidden="true"
                        className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-primary/25 bg-primary/8 text-xs font-bold text-primary"
                      >
                        {initials(patient.display_name)}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-xs font-semibold text-foreground">
                          {patient.display_name}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground">
                          {patient.age
                            ? `${patient.age} anos`
                            : "Idade não informada"}{" "}
                          • {patient.masked_cpf}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="max-w-48 px-3 py-3">
                    <p className="truncate text-xs text-foreground">
                      {maskPhone(patient.phone)}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {maskEmail(patient.email)}
                    </p>
                  </td>
                  <td className="px-3 py-3 text-xs text-muted-foreground">
                    {formatSession(patient.last_session)}
                  </td>
                  <td className="px-3 py-3 text-xs text-foreground">
                    {formatSession(patient.next_session)}
                  </td>
                  <td className="px-3 py-3">
                    <Badge variant={statusVariant[patient.status]}>
                      {patient.status_display}
                    </Badge>
                  </td>
                  <td className="px-3 py-3">
                    <PatientTags tags={patient.tags ?? []} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="divide-y divide-border md:hidden">
        {patients.map((patient) => {
          const selected = patient.id === selectedId;
          return (
            <button
              key={patient.id}
              type="button"
              onClick={() => onSelect(patient.id)}
              aria-pressed={selected}
              aria-label={`Selecionar paciente ${patient.display_name}`}
              className={`w-full p-4 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 ${
                selected
                  ? "bg-primary/8 shadow-[inset_3px_0_0_hsl(var(--primary))]"
                  : "hover:bg-secondary/45"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span
                    aria-hidden="true"
                    className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-primary/25 bg-primary/8 text-xs font-bold text-primary"
                  >
                    {initials(patient.display_name)}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {patient.display_name}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {patient.age
                        ? `${patient.age} anos`
                        : "Idade não informada"}{" "}
                      • {patient.masked_cpf}
                    </p>
                  </div>
                </div>
                <Badge variant={statusVariant[patient.status]}>
                  {patient.status_display}
                </Badge>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                <div>
                  <p className="font-semibold uppercase tracking-wide text-muted-foreground">
                    Contato
                  </p>
                  <p className="mt-1 truncate text-foreground">
                    {maskPhone(patient.phone)}
                  </p>
                </div>
                <div>
                  <p className="font-semibold uppercase tracking-wide text-muted-foreground">
                    Próxima sessão
                  </p>
                  <p className="mt-1 text-foreground">
                    {formatSession(patient.next_session)}
                  </p>
                </div>
              </div>

              <div className="mt-3">
                <PatientTags tags={patient.tags ?? []} />
              </div>
            </button>
          );
        })}
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border bg-secondary/20 px-4 py-3 text-xs text-muted-foreground">
        <span>
          Mostrando {patients.length} de {total} pacientes
        </span>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Página anterior"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </Button>
          <span>
            Página {page} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            aria-label="Próxima página"
          >
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </footer>
    </section>
  );
}
