"use client";

import {
  ChevronLeft,
  BookOpen,
  Plus,
  FileSpreadsheet,
  FileDown,
  User,
  Phone,
  Mail,
  Calendar,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { RecordSummary } from "../types";

interface RecordHeaderProps {
  summary: RecordSummary;
  exporting: boolean;
  onBack: () => void;
  onNewEvolution: () => void;
  onFillForm: () => void;
  onExport: () => void;
}

export function RecordHeader({
  summary,
  exporting,
  onBack,
  onNewEvolution,
  onFillForm,
  onExport,
}: RecordHeaderProps) {
  const patient = summary.patient;
  const initials = patient.full_name
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  return (
    <div className="space-y-4">
      {/* Cabeçalho do Prontuário */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground transition-all duration-200"
          title="Voltar para Pacientes"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Prontuário Clínico
            </h1>
            <p className="text-sm text-muted-foreground">
              Histórico detalhado do paciente com evoluções, consultas, arquivos e relatórios.
            </p>
          </div>
        </div>
      </div>

      {/* Card do Paciente com Ações */}
      <section className="overflow-hidden rounded-xl border border-border bg-card/60 backdrop-blur-xs p-5 shadow-xs transition-all duration-200 hover:border-primary/20">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

          {/* Informações do Paciente */}
          <div className="flex min-w-0 items-center gap-4">
            <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-primary/20 bg-primary/5 text-xl font-bold text-primary shadow-inner">
              {initials}
              <span className="absolute bottom-0 right-0 h-3.5 w-3.5 rounded-full border-2 border-card bg-success" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-xl font-bold text-foreground">
                  {patient.full_name}
                </h2>
                <span className="inline-flex items-center rounded-full bg-success/10 px-2.5 py-0.5 text-sm font-medium text-success">
                  {patient.status_display}
                </span>
              </div>

              <div className="mt-2.5 flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <User className="h-3.5 w-3.5 text-primary/60" />
                  {patient.age ? `${patient.age} anos` : "Idade não informada"}
                </span>
                <span className="flex items-center gap-1">
                  <Phone className="h-3.5 w-3.5 text-primary/60" />
                  {patient.phone || "Sem telefone"}
                </span>
                <span className="flex items-center gap-1">
                  <Mail className="h-3.5 w-3.5 text-primary/60" />
                  {patient.email || "Sem e-mail"}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-primary/60" />
                  Início: {new Date(summary.treatment_start).toLocaleDateString("pt-BR")}
                </span>
              </div>
            </div>
          </div>

          {/* Botões de Ação */}
          <div className="flex flex-wrap gap-2.5 lg:justify-end">
            <Button
              size="md"
              onClick={onNewEvolution}
              leftIcon={<Plus className="h-4 w-4" />}
              className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-xs"
            >
              Nova Evolução
            </Button>
            <Button
              size="md"
              variant="outline"
              onClick={onFillForm}
              leftIcon={<FileSpreadsheet className="h-4 w-4" />}
              className="border-primary/20 text-primary hover:bg-primary/10"
            >
              Preencher Formulário
            </Button>
            <Button
              size="md"
              variant="outline"
              isLoading={exporting}
              onClick={onExport}
              leftIcon={<FileDown className="h-4 w-4" />}
              className="border-primary/20 text-primary hover:bg-primary/10"
            >
              Gerar Documento
            </Button>
          </div>

        </div>
      </section>
    </div>
  );
}
