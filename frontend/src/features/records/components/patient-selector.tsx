"use client";

import { useEffect, useState } from "react";
import { Search, SlidersHorizontal, UserRound, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { usePatients } from "@/features/patients/hooks/use-patients";
import { cn } from "@/lib/utils";

interface PatientSelectorProps {
  selectedPatientId: number;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function PatientSelector({
  selectedPatientId,
  mobileOpen,
  onMobileClose,
}: PatientSelectorProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const { data, isLoading } = usePatients({
    search: debouncedSearch || undefined,
    status: "active",
    page_size: 20,
  });

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebouncedSearch(search.trim()), 250);
    return () => window.clearTimeout(timeout);
  }, [search]);

  const selectPatient = (id: number) => {
    router.push(`/dashboard/records/${id}`);
    onMobileClose();
  };

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          aria-label="Fechar lista de pacientes"
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm xl:hidden"
          onClick={onMobileClose}
        />
      )}
      <aside
        className={cn(
          "record-patient-selector fixed inset-y-0 left-0 z-50 flex w-[min(88vw,22rem)] flex-col border-r border-border bg-card p-4 shadow-2xl transition-transform xl:static xl:z-auto xl:w-auto xl:translate-x-0 xl:rounded-xl xl:border xl:shadow-none",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Navegação entre prontuários"
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-bold text-foreground">Prontuários</h2>
            <p className="mt-1 text-xs text-muted-foreground">Pacientes em acompanhamento</p>
          </div>
          <button
            type="button"
            className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground xl:hidden"
            onClick={onMobileClose}
            aria-label="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 flex gap-2">
          <label className="relative flex-1">
            <span className="sr-only">Buscar paciente</span>
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar paciente..."
              className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15"
            />
          </label>
          <button
            type="button"
            className="grid h-10 w-10 place-items-center rounded-md border border-border bg-background text-muted-foreground"
            aria-label="Filtros disponíveis: pacientes ativos"
            title="Exibindo pacientes ativos"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
          {isLoading &&
            Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-lg bg-secondary" />
            ))}

          {!isLoading && data?.results.length === 0 && (
            <div className="rounded-lg border border-dashed border-border p-6 text-center">
              <UserRound className="mx-auto h-5 w-5 text-muted-foreground" />
              <p className="mt-3 text-xs font-semibold">Nenhum paciente encontrado</p>
              <p className="mt-1 text-[11px] text-muted-foreground">Revise o termo pesquisado.</p>
            </div>
          )}

          {data?.results.map((patient) => {
            const selected = patient.id === selectedPatientId;
            return (
              <button
                key={patient.id}
                type="button"
                onClick={() => selectPatient(patient.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition",
                  selected
                    ? "border-primary/35 bg-primary/10 text-foreground"
                    : "border-transparent text-muted-foreground hover:border-border hover:bg-secondary/70 hover:text-foreground",
                )}
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-border bg-background text-xs font-bold text-primary">
                  {patient.full_name
                    .split(" ")
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join("")}
                </span>
                <span className="min-w-0 flex-1">
                  <strong className="block truncate text-xs">{patient.full_name}</strong>
                  <small className="mt-1 block truncate text-[10px] text-muted-foreground">
                    {patient.age ? `${patient.age} anos` : "Idade não informada"}
                    {patient.phone ? ` · ${patient.phone}` : ""}
                  </small>
                </span>
                {selected && <span className="h-2 w-2 rounded-full bg-primary" />}
              </button>
            );
          })}
        </div>

        {data && data.count > data.results.length && (
          <p className="mt-3 border-t border-border pt-3 text-center text-[10px] text-muted-foreground">
            Exibindo {data.results.length} de {data.count} pacientes. Use a busca para localizar outros.
          </p>
        )}
      </aside>
    </>
  );
}
