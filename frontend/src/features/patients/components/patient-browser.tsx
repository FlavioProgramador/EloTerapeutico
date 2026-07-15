"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  Settings2,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { PatientDashboardItem, PatientMetrics } from "../types";
import { PatientMetricsGrid } from "./patient-metrics";

interface PatientPage {
  pagination: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  results: PatientDashboardItem[];
}

interface PanelData {
  patient: PatientDashboardItem;
  next_session: null | {
    id: number;
    start_time: string;
    end_time: string;
    status: string;
  };
  follow_up: {
    total_sessions: number;
    missed_sessions: number;
    attendance_percentage: number | null;
    active_goals: number;
  };
}

function formatDate(value?: string | null) {
  if (!value) return "Não agendado";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function PatientBrowser() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<number>();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, 350);
    return () => window.clearTimeout(timer);
  }, [search]);

  const list = useQuery({
    queryKey: ["patients", "secure-browser", debouncedSearch, status, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "6",
      });
      if (debouncedSearch) params.set("search", debouncedSearch);
      if (status) params.set("status", status);
      const response = await api.get<PatientPage>(
        `patients/?${params.toString()}`,
      );
      return response.data;
    },
  });

  const metrics = useQuery({
    queryKey: ["patients", "dashboard-metrics"],
    queryFn: async () => {
      const response = await api.get<PatientMetrics>(
        "patients/dashboard-metrics/",
      );
      return response.data;
    },
  });

  const panel = useQuery({
    queryKey: ["patients", selectedId, "administrative-panel"],
    queryFn: async () => {
      const response = await api.get<PanelData>(
        `patients/${selectedId}/dashboard/`,
      );
      return response.data;
    },
    enabled: Boolean(selectedId),
  });

  const patients = list.data?.results ?? [];
  useEffect(() => {
    if (!selectedId && patients[0]) setSelectedId(patients[0].id);
  }, [patients, selectedId]);

  return (
    <div className="space-y-4">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Pacientes
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Gerencie cadastros, contatos e acompanhamentos.
          </p>
        </div>
        <Button
          onClick={() => router.push("/dashboard/patients/new")}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Novo paciente
        </Button>
      </header>

      <PatientMetricsGrid metrics={metrics.data} />

      <section className="grid gap-3 rounded-xl border border-border bg-card p-3 md:grid-cols-[minmax(0,1fr)_13rem]">
        <label className="relative">
          <span className="sr-only">Buscar pacientes</span>
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por nome, CPF, telefone ou e-mail..."
            className="h-10 w-full rounded-md border border-border bg-background pl-9 pr-3 text-xs outline-none focus:border-primary"
          />
        </label>
        <select
          value={status}
          onChange={(event) => {
            setStatus(event.target.value);
            setPage(1);
          }}
          className="h-10 rounded-md border border-border bg-background px-3 text-xs"
        >
          <option value="">Todos os status</option>
          <option value="active">Ativos</option>
          <option value="evaluation">Em avaliação</option>
          <option value="waiting_return">Aguardando retorno</option>
          <option value="discharged">Alta</option>
          <option value="inactive">Encerrados</option>
        </select>
      </section>

      <div className="grid items-start gap-4 xl:grid-cols-[minmax(0,1.85fr)_minmax(20rem,1fr)]">
        <section className="overflow-hidden rounded-xl border border-border bg-card">
          {list.isLoading ? (
            <div className="h-72 animate-pulse bg-secondary" />
          ) : patients.length === 0 ? (
            <div className="grid min-h-72 place-items-center p-8 text-center text-xs text-muted-foreground">
              Nenhum paciente encontrado.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {patients.map((patient) => (
                <button
                  key={patient.id}
                  type="button"
                  onClick={() => setSelectedId(patient.id)}
                  className={`grid w-full gap-3 p-4 text-left transition hover:bg-secondary/40 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto] ${
                    selectedId === patient.id ? "bg-primary/5" : ""
                  }`}
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {initials(patient.display_name)}
                    </span>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-foreground">
                        {patient.display_name}
                      </p>
                      <p className="mt-1 text-[10px] text-muted-foreground">
                        {patient.masked_cpf}
                      </p>
                    </div>
                  </div>
                  <div className="min-w-0 text-[11px] text-muted-foreground">
                    <p className="truncate">
                      {patient.phone || "Sem telefone"}
                    </p>
                    <p className="truncate">{patient.email || "Sem e-mail"}</p>
                  </div>
                  <Badge
                    variant={
                      patient.status === "active" ? "success" : "outline"
                    }
                  >
                    {patient.status_display}
                  </Badge>
                </button>
              ))}
            </div>
          )}

          <footer className="flex items-center justify-between border-t border-border px-4 py-3 text-[11px] text-muted-foreground">
            <span>
              Mostrando {patients.length} de {list.data?.pagination.count ?? 0}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                disabled={!list.data?.pagination.previous}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                aria-label="Página anterior"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span>
                {list.data?.pagination.current_page ?? page} de{" "}
                {list.data?.pagination.total_pages ?? 1}
              </span>
              <Button
                variant="outline"
                size="icon"
                disabled={!list.data?.pagination.next}
                onClick={() => setPage((current) => current + 1)}
                aria-label="Próxima página"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </footer>
        </section>

        <aside className="rounded-xl border border-border bg-card p-4">
          {panel.isLoading ? (
            <div className="h-64 animate-pulse rounded-lg bg-secondary" />
          ) : panel.data ? (
            <div className="space-y-4">
              <div>
                <h2 className="font-bold text-foreground">
                  {panel.data.patient.display_name}
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  {panel.data.patient.phone || "Telefone não informado"}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-secondary/20 p-3">
                <p className="flex items-center gap-2 text-[10px] font-semibold text-muted-foreground">
                  <CalendarDays className="h-4 w-4 text-primary" /> Próxima
                  sessão
                </p>
                <p className="mt-2 text-xs font-medium text-foreground">
                  {formatDate(panel.data.next_session?.start_time)}
                </p>
              </div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() =>
                  router.push(`/dashboard/patients/${panel.data.patient.id}`)
                }
                leftIcon={<Settings2 className="h-4 w-4" />}
              >
                Editar ou arquivar cadastro
              </Button>
            </div>
          ) : (
            <p className="text-center text-xs text-muted-foreground">
              Selecione um paciente.
            </p>
          )}
        </aside>
      </div>
    </div>
  );
}
