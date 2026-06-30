"use client";

import {
  Download,
  FilePlus2,
  Menu,
  Paperclip,
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { RecordSummary } from "../types";

interface RecordHeaderProps {
  summary: RecordSummary;
  exporting: boolean;
  onOpenPatients: () => void;
  onNewEvolution: () => void;
  onOpenAnamnesis: () => void;
  onOpenDocuments: () => void;
  onExport: () => void;
}

export function RecordHeader({
  summary,
  exporting,
  onOpenPatients,
  onNewEvolution,
  onOpenAnamnesis,
  onOpenDocuments,
  onExport,
}: RecordHeaderProps) {
  const patient = summary.patient;
  const initials = patient.full_name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("");

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-3">
          <button
            type="button"
            onClick={onOpenPatients}
            className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-emerald-400/25 bg-emerald-500/10 text-emerald-300 transition hover:bg-emerald-500/15 xl:hidden"
            aria-label="Abrir lista de pacientes"
          >
            <Menu className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Prontuário Eletrônico
            </h1>
            <p className="mt-1 text-xs text-muted-foreground">
              Acompanhe anamnese, evoluções, objetivos e documentos do paciente.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={onNewEvolution}
            leftIcon={<FilePlus2 className="h-4 w-4" />}
            className="bg-emerald-500 text-emerald-950 shadow-sm hover:bg-emerald-400"
          >
            Nova evolução
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onOpenAnamnesis}
            leftIcon={<UserRound className="h-4 w-4" />}
            className="border-sky-400/25 text-sky-200 hover:bg-sky-500/10 hover:text-sky-100"
          >
            Anamnese
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={onOpenDocuments}
            leftIcon={<Paperclip className="h-4 w-4" />}
            className="border-violet-400/25 text-violet-200 hover:bg-violet-500/10 hover:text-violet-100"
          >
            Anexar documento
          </Button>
          <Button
            size="sm"
            variant="outline"
            isLoading={exporting}
            onClick={onExport}
            leftIcon={<Download className="h-4 w-4" />}
            className="border-amber-400/25 text-amber-200 hover:bg-amber-500/10 hover:text-amber-100"
          >
            Exportar PDF
          </Button>
        </div>
      </div>

      <section className="overflow-hidden rounded-xl border border-emerald-400/20 bg-gradient-to-br from-emerald-500/10 via-card to-sky-500/5 p-4 shadow-xs">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-center gap-4">
            <span className="grid h-14 w-14 shrink-0 place-items-center rounded-full border border-emerald-300/45 bg-emerald-500/15 text-lg font-bold text-emerald-200 shadow-sm">
              {initials}
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="truncate text-lg font-bold text-foreground">
                  {patient.full_name}
                </h2>
                <span className="rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                  {patient.status_display}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                <span className="rounded-md border border-emerald-400/15 bg-emerald-500/5 px-2.5 py-1.5">
                  {patient.age ? `${patient.age} anos` : "Idade não informada"}
                </span>
                <span className="rounded-md border border-sky-400/15 bg-sky-500/5 px-2.5 py-1.5">
                  {patient.phone || "Telefone não informado"}
                </span>
                <span className="max-w-full truncate rounded-md border border-violet-400/15 bg-violet-500/5 px-2.5 py-1.5">
                  {patient.email || "E-mail não informado"}
                </span>
              </div>
            </div>
          </div>

          <dl className="grid grid-cols-2 gap-4 border-t border-emerald-400/15 pt-4 text-xs lg:min-w-[22rem] lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
            <div>
              <dt className="text-muted-foreground">Início do acompanhamento</dt>
              <dd className="mt-1 font-semibold text-emerald-300">
                {new Date(summary.treatment_start).toLocaleDateString("pt-BR")}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Última atualização</dt>
              <dd className="mt-1 font-semibold text-sky-300">
                {new Date(summary.last_update).toLocaleDateString("pt-BR")}
              </dd>
            </div>
          </dl>
        </div>
      </section>
    </div>
  );
}
