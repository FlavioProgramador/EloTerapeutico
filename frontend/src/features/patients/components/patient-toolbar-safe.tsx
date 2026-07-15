import {
  Download,
  Plus,
  Search,
  SlidersHorizontal,
  Upload,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { PatientStatus } from "../types";

export interface SafeToolbarFilters {
  search: string;
  status: "all" | PatientStatus;
  modality: string;
  payerType: string;
  tag: string;
  noNextSession: boolean;
}

interface Props {
  filters: SafeToolbarFilters;
  advancedOpen: boolean;
  exporting: boolean;
  canImport: boolean;
  onChange: (filters: SafeToolbarFilters) => void;
  onAdvanced: () => void;
  onNew: () => void;
  onImport: () => void;
  onExport: () => void;
}

export function PatientToolbarSafe(props: Props) {
  const update = <K extends keyof SafeToolbarFilters>(
    key: K,
    value: SafeToolbarFilters[K],
  ) => props.onChange({ ...props.filters, [key]: value });

  return (
    <div className="space-y-3">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Pacientes
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Gerencie cadastros, contatos e acompanhamentos.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {props.canImport && (
            <Button
              variant="outline"
              size="sm"
              onClick={props.onImport}
              leftIcon={<Upload className="h-4 w-4" />}
            >
              Importar
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            isLoading={props.exporting}
            onClick={props.onExport}
            leftIcon={<Download className="h-4 w-4" />}
          >
            Exportar
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={props.onAdvanced}
            leftIcon={<SlidersHorizontal className="h-4 w-4" />}
          >
            Filtros
          </Button>
          <Button
            size="sm"
            onClick={props.onNew}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Novo paciente
          </Button>
        </div>
      </header>

      <section className="rounded-xl border border-border bg-card p-3">
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_12rem]">
          <label className="relative">
            <span className="sr-only">Buscar pacientes</span>
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={props.filters.search}
              onChange={(event) => update("search", event.target.value)}
              placeholder="Buscar por nome, CPF, telefone ou e-mail..."
              className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none focus:border-primary"
            />
          </label>
          <select
            value={props.filters.status}
            onChange={(event) =>
              update(
                "status",
                event.target.value as SafeToolbarFilters["status"],
              )
            }
            className="h-10 rounded-md border border-border bg-background px-3 text-xs text-foreground"
          >
            <option value="all">Todos os status</option>
            <option value="active">Ativos</option>
            <option value="evaluation">Em avaliação</option>
            <option value="waiting_return">Aguardando retorno</option>
            <option value="discharged">Alta</option>
            <option value="inactive">Encerrados</option>
          </select>
        </div>

        {props.advancedOpen && (
          <div className="mt-3 grid gap-3 border-t border-border pt-3 sm:grid-cols-2 xl:grid-cols-4">
            <select
              value={props.filters.modality}
              onChange={(event) => update("modality", event.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-xs"
            >
              <option value="">Todas as modalidades</option>
              <option value="in_person">Presencial</option>
              <option value="online">Online</option>
              <option value="hybrid">Híbrido</option>
            </select>
            <select
              value={props.filters.payerType}
              onChange={(event) => update("payerType", event.target.value)}
              className="h-9 rounded-md border border-border bg-background px-3 text-xs"
            >
              <option value="">Todos os atendimentos</option>
              <option value="private">Particular</option>
              <option value="insurance">Convênio</option>
            </select>
            <input
              value={props.filters.tag}
              onChange={(event) => update("tag", event.target.value)}
              placeholder="Etiqueta"
              className="h-9 rounded-md border border-border bg-background px-3 text-xs"
            />
            <label className="flex h-9 items-center gap-2 rounded-md border border-border px-3 text-xs">
              <input
                type="checkbox"
                checked={props.filters.noNextSession}
                onChange={(event) =>
                  update("noNextSession", event.target.checked)
                }
              />
              Sem próxima sessão
            </label>
          </div>
        )}
      </section>
    </div>
  );
}
