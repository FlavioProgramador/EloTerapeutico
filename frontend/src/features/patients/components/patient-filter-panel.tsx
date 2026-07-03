import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { User } from "@/contexts/auth";
import {
  PATIENT_FILTER_SELECTS,
  type PatientListFilters,
} from "./patient-list-config";

interface Props {
  filters: PatientListFilters;
  userRole?: User["role"];
  onChange: (filters: PatientListFilters) => void;
  onApply: () => void;
  onClear: () => void;
  onClose: () => void;
}

const INPUTS = [
  ["insurance", "Convênio", "Nome do convênio", "text"],
  ["tag", "Etiqueta", "Ex.: ansiedade", "text"],
  ["createdFrom", "Cadastro a partir de", "", "date"],
  ["createdTo", "Cadastro até", "", "date"],
  ["birthFrom", "Nascimento a partir de", "", "date"],
  ["birthTo", "Nascimento até", "", "date"],
] as const;

export function PatientFilterPanel({
  filters,
  userRole,
  onChange,
  onApply,
  onClear,
  onClose,
}: Props) {
  const update = <K extends keyof PatientListFilters>(
    key: K,
    value: PatientListFilters[K],
  ) => onChange({ ...filters, [key]: value });

  return (
    <div className="mt-3 border-t border-border pt-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-foreground">
            Filtros avançados
          </h2>
          <p className="mt-1 text-[11px] text-muted-foreground">
            Combine critérios administrativos para refinar a listagem.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground transition hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
          aria-label="Fechar filtros"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {PATIENT_FILTER_SELECTS.map(({ key, label, options }) => (
          <label key={key} className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            {label}
            <select
              value={String(filters[key])}
              onChange={(event) =>
                update(key, event.target.value as PatientListFilters[typeof key])
              }
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs font-normal text-foreground"
            >
              {options.map(([value, text]) => (
                <option key={value} value={value}>{text}</option>
              ))}
            </select>
          </label>
        ))}

        {userRole !== "therapist" && (
          <label className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            Profissional (ID)
            <input
              inputMode="numeric"
              value={filters.therapist}
              onChange={(event) =>
                update("therapist", event.target.value.replace(/\D/g, ""))
              }
              placeholder="ID do profissional"
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs font-normal text-foreground"
            />
          </label>
        )}

        {INPUTS.map(([key, label, placeholder, type]) => (
          <label key={key} className="space-y-1 text-[10px] font-semibold text-muted-foreground">
            {label}
            <input
              type={type}
              value={String(filters[key])}
              onChange={(event) => update(key, event.target.value)}
              placeholder={placeholder}
              className="h-10 w-full rounded-md border border-border bg-background px-3 text-xs font-normal text-foreground"
            />
          </label>
        ))}

        <label className="flex h-10 items-center gap-2 self-end rounded-md border border-border bg-background px-3 text-xs text-foreground">
          <input
            type="checkbox"
            checked={filters.noNextSession}
            onChange={(event) => update("noNextSession", event.target.checked)}
            className="accent-primary"
          />
          Sem próxima sessão
        </label>
      </div>

      <div className="mt-4 flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:justify-end">
        <Button size="sm" variant="ghost" onClick={onClear}>Limpar filtros</Button>
        <Button size="sm" onClick={onApply}>Aplicar filtros</Button>
      </div>
    </div>
  );
}
