import {
  Download,
  Filter,
  Plus,
  Search,
  SlidersHorizontal,
  Upload,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { PatientStatus } from "../types";

export interface PatientToolbarFilters {
  search: string;
  status: "all" | PatientStatus;
  modality: string;
  payerType: string;
  tag: string;
  noNextSession: boolean;
}

interface Props {
  filters: PatientToolbarFilters;
  advancedOpen: boolean;
  exporting: boolean;
  onFiltersChange: (filters: PatientToolbarFilters) => void;
  onAdvancedToggle: () => void;
  onNew: () => void;
  onImport: () => void;
  onExport: () => void;
}

const statusTabs: Array<[PatientToolbarFilters["status"], string]> = [
  ["all", "Todos"],
  ["active", "Ativos"],
  ["evaluation", "Em avaliação"],
  ["waiting_return", "Aguardando retorno"],
  ["discharged", "Alta"],
];

export function PatientToolbar({
  filters,
  advancedOpen,
  exporting,
  onFiltersChange,
  onAdvancedToggle,
  onNew,
  onImport,
  onExport,
}: Props) {
  const update = <K extends keyof PatientToolbarFilters>(
    key: K,
    value: PatientToolbarFilters[K],
  ) => onFiltersChange({ ...filters, [key]: value });

  const clear = () =>
    onFiltersChange({
      search: "",
      status: "all",
      modality: "",
      payerType: "",
      tag: "",
      noNextSession: false,
    });

  const hasAdvanced = Boolean(
    filters.modality || filters.payerType || filters.tag || filters.noNextSession,
  );

  return (
    <div className="space-y-3">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Pacientes
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Gerencie cadastros, prontuários, contatos e acompanhamentos dos pacientes.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={onImport} leftIcon={<Upload className="h-4 w-4" />}>
            Importar
          </Button>
          <Button variant="outline" size="sm" isLoading={exporting} onClick={onExport} leftIcon={<Download className="h-4 w-4" />}>
            Exportar
          </Button>
          <Button variant="outline" size="sm" onClick={onAdvancedToggle} leftIcon={<SlidersHorizontal className="h-4 w-4" />}>
            Filtros avançados
          </Button>
          <Button size="sm" onClick={onNew} leftIcon={<Plus className="h-4 w-4" />}>
            Novo paciente
          </Button>
        </div>
      </header>

      <section className="overflow-hidden rounded-xl border border-border bg-card">
        <div className="flex gap-1 overflow-x-auto border-b border-border p-2">
          {statusTabs.map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => update("status", value)}
              className={`min-w-max rounded-md px-3 py-2 text-[10px] font-semibold transition ${
                filters.status === value
                  ? "bg-primary/12 text-primary"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              aria-pressed={filters.status === value}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-3 p-3 md:flex-row md:items-center">
          <label className="relative flex-1">
            <span className="sr-only">Buscar pacientes</span>
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={filters.search}
              onChange={(event) => update("search", event.target.value)}
              placeholder="Buscar por nome, CPF, telefone ou e-mail..."
              className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15"
            />
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={clear}
            disabled={!filters.search && filters.status === "all" && !hasAdvanced}
            leftIcon={<X className="h-3.5 w-3.5" />}
          >
            Limpar filtros
          </Button>
        </div>

        {advancedOpen && (
          <div className="grid gap-3 border-t border-border bg-secondary/20 p-3 sm:grid-cols-2 xl:grid-cols-4">
            <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
              Modalidade
              <select
                value={filters.modality}
                onChange={(event) => update("modality", event.target.value)}
                className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground"
              >
                <option value="">Todas</option>
                <option value="in_person">Presencial</option>
                <option value="online">Online</option>
                <option value="hybrid">Híbrido</option>
              </select>
            </label>
            <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
              Atendimento
              <select
                value={filters.payerType}
                onChange={(event) => update("payerType", event.target.value)}
                className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground"
              >
                <option value="">Particular ou convênio</option>
                <option value="private">Particular</option>
                <option value="insurance">Convênio</option>
              </select>
            </label>
            <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
              Etiqueta
              <input
                value={filters.tag}
                onChange={(event) => update("tag", event.target.value)}
                placeholder="Ex.: ansiedade"
                className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground"
              />
            </label>
            <label className="flex h-9 items-center gap-2 self-end rounded-md border border-border bg-background px-3 text-xs text-foreground">
              <input
                type="checkbox"
                checked={filters.noNextSession}
                onChange={(event) => update("noNextSession", event.target.checked)}
                className="accent-primary"
              />
              Sem próxima sessão
            </label>
          </div>
        )}
      </section>
    </div>
  );
}
