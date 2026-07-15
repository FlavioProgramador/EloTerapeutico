"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Calendar,
  Clock,
  Video,
  User,
  FileEdit,
  Eye,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { agendaService } from "@/features/agenda/services/agenda.service";
import type { Appointment } from "@/types";

interface AppointmentsTabProps {
  patientId: number;
  onNewEvolution: (appointmentId: number) => void;
  onViewEvolution: (evolutionId: number) => void;
}

export function AppointmentsTab({
  patientId,
  onNewEvolution,
  onViewEvolution,
}: AppointmentsTabProps) {
  const [page, setPage] = useState(1);

  // Busca as consultas do paciente usando TanStack Query
  const {
    data: appointments = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["records", patientId, "appointments", page],
    queryFn: () => agendaService.list({ patient: patientId, page }),
    enabled: Number.isFinite(patientId) && patientId > 0,
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "scheduled":
        return (
          <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-700 dark:text-blue-300">
            Agendada
          </span>
        );
      case "confirmed":
        return (
          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:text-amber-300">
            Confirmada
          </span>
        );
      case "completed":
        return (
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:text-emerald-300">
            Realizada
          </span>
        );
      case "cancelled":
        return (
          <span className="inline-flex items-center rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-700 dark:text-red-300">
            Cancelada
          </span>
        );
      case "missed":
        return (
          <span className="inline-flex items-center rounded-full bg-gray-500/10 px-2 py-0.5 text-[10px] font-medium text-gray-700 dark:text-gray-300">
            Faltou
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-full bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-700 dark:text-slate-300">
            {status}
          </span>
        );
    }
  };

  const getEvolutionBadge = (appointment: Appointment) => {
    if (appointment.evolution_id) {
      const isDraft = appointment.evolution_status === "draft";
      return (
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
            isDraft
              ? "bg-amber-500/10 text-amber-700 dark:text-amber-300"
              : "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
          }`}
        >
          {isDraft ? "Rascunho" : "Finalizada"}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center rounded-full bg-slate-500/10 px-2 py-0.5 text-[10px] font-medium text-slate-500">
        Pendente
      </span>
    );
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <SkeletonTable rows={5} />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle className="h-8 w-8 text-destructive mb-2" />
        <h3 className="text-sm font-semibold text-foreground">
          Erro ao carregar consultas
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          Ocorreu um erro ao buscar o histórico de consultas.
        </p>
        <Button
          size="sm"
          variant="outline"
          className="mt-4"
          onClick={() => refetch()}
        >
          Tentar novamente
        </Button>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      {appointments.length === 0 ? (
        <div className="py-12">
          <EmptyState
            icon={<Calendar className="h-6 w-6 text-muted-foreground" />}
            title="Nenhuma consulta registrada"
            description="Não há consultas agendadas ou realizadas para este paciente no histórico."
          />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data & Hora</TableHead>
                <TableHead>Profissional</TableHead>
                <TableHead>Status Consulta</TableHead>
                <TableHead>Evolução</TableHead>
                <TableHead className="w-[120px] text-right">Ação</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {appointments.map((appointment) => {
                const dateObj = new Date(appointment.start_time);
                const isCompleted = appointment.status === "completed";
                const hasEvolution = !!appointment.evolution_id;

                return (
                  <TableRow key={appointment.id}>
                    <TableCell className="font-medium text-foreground">
                      <div className="flex flex-col">
                        <span className="flex items-center gap-1.5 font-semibold text-foreground">
                          <Calendar className="h-3.5 w-3.5 text-emerald-600/70" />
                          {dateObj.toLocaleDateString("pt-BR")}
                        </span>
                        <span className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                          {dateObj.toLocaleTimeString("pt-BR", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                        <User className="h-3.5 w-3.5 text-slate-400" />
                        {appointment.therapist_name || "Profissional"}
                      </span>
                    </TableCell>
                    <TableCell>{getStatusBadge(appointment.status)}</TableCell>
                    <TableCell>{getEvolutionBadge(appointment)}</TableCell>
                    <TableCell className="text-right">
                      {hasEvolution ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            onViewEvolution(appointment.evolution_id!)
                          }
                          title="Visualizar evolução vinculada"
                          className="h-8 w-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-500/10"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      ) : isCompleted ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onNewEvolution(appointment.id)}
                          title="Evoluir consulta realizada"
                          className="h-8 w-8 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-500/10"
                        >
                          <FileEdit className="h-4 w-4" />
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          --
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </Card>
  );
}
