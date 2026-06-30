import { Cake, Download, Search, SlidersHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { User } from "@/contexts/auth";
import { PatientFilterPanel } from "./patient-filter-panel";
import type { PatientListFilters } from "./patient-list-config";

interface Props {
  search: string;
  filters: PatientListFilters;
  draftFilters: PatientListFilters;
  userRole?: User["role"];
  filtersOpen: boolean;
  birthdaysOnly: boolean;
  filterCount: number;
  exporting: boolean;
  onSearchChange: (value: string) => void;
  onDraftFiltersChange: (filters: PatientListFilters) => void;
  onToggleFilters: () => void;
  onToggleBirthdays: () => void;
  onApplyFilters: () => void;
  onClearFilters: () => void;
  onExport: () => void;
}

export function PatientToolbarReference(props: Props) {
  return (
    <section className="rounded-xl border border-border bg-card p-3">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
        <label className="relative min-w-0 flex-1">
          <span className="sr-only">Buscar pacientes</span>
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={props.search}
            onChange={(event) => props.onSearchChange(event.target.value)}
            placeholder="Buscar por nome, CPF, telefone ou e-mail..."
            className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15"
          />
        </label>

        <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
          <Button
            size="sm"
            variant={props.birthdaysOnly ? "secondary" : "outline"}
            onClick={props.onToggleBirthdays}
            leftIcon={<Cake className="h-4 w-4" />}
            aria-pressed={props.birthdaysOnly}
          >
            Aniversariantes
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={props.onToggleFilters}
            leftIcon={<SlidersHorizontal className="h-4 w-4" />}
            aria-expanded={props.filtersOpen}
          >
            Filtros
            {props.filterCount > 0 && (
              <span className="ml-1 grid h-5 min-w-5 place-items-center rounded-full bg-primary px-1 text-[10px] text-primary-foreground">
                {props.filterCount}
              </span>
            )}
          </Button>
          <Button
            className="col-span-2 sm:col-auto"
            size="sm"
            variant="outline"
            onClick={props.onExport}
            isLoading={props.exporting}
            leftIcon={<Download className="h-4 w-4" />}
          >
            Exportar
          </Button>
        </div>
      </div>

      {props.filtersOpen && (
        <PatientFilterPanel
          filters={props.draftFilters}
          userRole={props.userRole}
          onChange={props.onDraftFiltersChange}
          onApply={props.onApplyFilters}
          onClear={props.onClearFilters}
          onClose={props.onToggleFilters}
        />
      )}
    </section>
  );
}
