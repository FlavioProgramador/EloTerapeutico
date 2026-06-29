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

const avatarTones = [
  "border-emerald-400/25 bg-emerald-500/10 text-emerald-300",
  "border-sky-400/25 bg-sky-500/10 text-sky-300",
  "border-violet-400/25 bg-violet-500/10 text-violet-300",
  "border-rose-400/25 bg-rose-500/10 text-rose-300",
  "border-amber-400/25 bg-amber-500/10 text-amber-300",
  "border-cyan-400/25 bg-cyan-500/10 text-cyan-300",
];

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
    const timeout = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      250,
    );
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
          "record-patient-selector fixed inset-y-0 left-0 z-50 flex w-[min(88vw,22rem)] flex-col border-r border-emerald-400/15 bg-gradient-to-b from-card via-card to-emerald-950/20 p-4 shadow-2xl transition-transform xl:static xl:z-auto xl:w-auto xl:translate-x-0 xl:rounded-xl xl:border xl:shadow-none",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Navegação entre prontuários"
      >
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-sm" />
              <h2 className="text-sm font-bold text-foreground">Prontuários</h2>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Pacientes em acompanhamento
            </p>
          </div>
          <button
            type="button"
            className="rounded-md p-2 text-muted-foreground hover:bg-emerald-500/10 hover:text-emerald-200 xl:hidden"
            onClick={onMobileClose}
            aria-label="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 flex gap-2">
          <label className="relative flex-1">
            <span className="sr-only">Buscar paciente</span>
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-emerald-300/80" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar paciente..."
              className="h-10 w-full rounded-md border border-emerald-400/15 bg-background/75 pl-9 pr-3 text-xs text-foreground outline-none transition placeholder:text-muted-foreground/70 focus:border-emerald-400/50 focus:ring-2 focus:ring-emerald-400/10"
            />
          </label>
          <button
            type="button"
            className="grid h-10 w-10 place-items-center rounded-md border border-sky-400/20 bg-sky-500/5 text-sky-300 transition hover:bg-sky-500/10"
            aria-label="Filtros disponíveis: pacientes ativos"
            title="Exibindo pacientes ativos"
          >
            <SlidersHorizontal className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
          {isLoading &&
            Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-16 animate-pulse rounded-lg bg-secondary"
              />
            ))}

          {!isLoading && data?.results.length === 0 && (
            <div className="rounded-lg border border-dashed border-emerald-400/20 bg-emerald-500/5 p-6 text-center">
              <UserRound className="mx-auto h-5 w-5 text-emerald-300" />
              <p className="mt-3 text-xs font-semibold">
                Nenhum paciente encontrado
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Revise o termo pesquisado.
              </p>
            </div>
          )}

          {data?.results.map((patient, index) => {
            const selected = patient.id === selectedPatientId;
            return (
              <button
                key={patient.id}
                type="button"
                onClick={() => selectPatient(patient.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition",
                  selected
                    ? "border-emerald-400/35 bg-gradient-to-r from-emerald-500/15 to-cyan-500/10 text-foreground shadow-sm"
                    : "border-transparent text-muted-foreground hover:border-sky-400/15 hover:bg-sky-500/5 hover:text-foreground",
                )}
              >
                <span
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-full border text-xs font-bold",
                    selected
                      ? "border-emerald-300/40 bg-emerald-500/15 text-emerald-200"
                      : avatarTones[index % avatarTones.length],
                  )}
                >
                  {patient.full_name
                    .split(" ")
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join("")}
                </span>
                <span className="min-w-0 flex-1">
                  <strong className="block truncate text-xs">
                    {patient.full_name}
                  </strong>
                  <small className="mt-1 block truncate text-[10px] text-muted-foreground">
                    {patient.age ? `${patient.age} anos` : "Idade não informada"}
                    {patient.phone ? ` · ${patient.phone}` : ""}
                  </small>
                </span>
                {selected && (
                  <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-sm" />
                )}
              </button>
            );
          })}
        </div>

        {data && data.count > data.results.length && (
          <p className="mt-3 border-t border-emerald-400/15 pt-3 text-center text-[10px] text-muted-foreground">
            Exibindo {data.results.length} de {data.count} pacientes. Use a busca
            para localizar outros.
          </p>
        )}
      </aside>
    </>
  );
}
