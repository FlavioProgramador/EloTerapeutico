"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Calendar, Clock, Eye, FileEdit, User } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonTable } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
  const [page] = useState(1);
  const query = useQuery({
    queryKey: ["records", patientId, "appointments", page],
    queryFn: async (): Promise<Appointment[]> => {
      const response = await agendaService.appointments.list({
        patient: patientId,
        page,
      });
      return response.results as unknown as Appointment[];
    },
    enabled: Number.isFinite(patientId) && patientId > 0,
  });
  const appointments = query.data || [];

  if (query.isLoading) {
    return (
      <Card className="p-6">
        <SkeletonTable rows={5} />
      </Card>
    );
  }

  if (query.isError) {
    return (
      <Card className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle className="mb-2 size-8 text-destructive" />
        <h3 className="text-sm font-semibold">Erro ao carregar consultas</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Não foi possível consultar o histórico de atendimentos.
        </p>
        <Button
          size="sm"
          variant="outline"
          className="mt-4"
          onClick={() => query.refetch()}
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
            icon={<Calendar className="size-6 text-muted-foreground" />}
            title="Nenhuma consulta registrada"
            description="Não há consultas agendadas ou realizadas para este paciente."
          />
        </div>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data e hora</TableHead>
                <TableHead>Profissional</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Evolução</TableHead>
                <TableHead className="text-right">Ação</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {appointments.map((appointment) => {
                const date = new Date(appointment.start_time);
                const hasEvolution = Boolean(appointment.evolution_id);
                return (
                  <TableRow key={appointment.id}>
                    <TableCell>
                      <strong className="flex items-center gap-1.5 text-sm">
                        <Calendar className="size-3.5 text-primary" />
                        {date.toLocaleDateString("pt-BR")}
                      </strong>
                      <span className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock className="size-3.5" />
                        {date.toLocaleTimeString("pt-BR", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="flex items-center gap-1.5 text-xs font-medium">
                        <User className="size-3.5 text-muted-foreground" />
                        {appointment.therapist_name || "Profissional"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <StatusLabel status={appointment.status} />
                    </TableCell>
                    <TableCell>
                      <span className="text-xs text-muted-foreground">
                        {hasEvolution
                          ? appointment.evolution_status === "draft"
                            ? "Rascunho"
                            : "Finalizada"
                          : "Pendente"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {hasEvolution ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            onViewEvolution(appointment.evolution_id!)
                          }
                          aria-label="Visualizar evolução"
                        >
                          <Eye className="size-4" />
                        </Button>
                      ) : appointment.status === "completed" ? (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onNewEvolution(appointment.id)}
                          aria-label="Registrar evolução"
                        >
                          <FileEdit className="size-4" />
                        </Button>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
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

function StatusLabel({ status }: { status: string }) {
  const labels: Record<string, string> = {
    scheduled: "Agendada",
    confirmed: "Confirmada",
    completed: "Realizada",
    cancelled: "Cancelada",
    missed: "Faltou",
    rescheduled: "Remarcada",
  };
  return (
    <span className="inline-flex rounded-full border border-border bg-secondary/40 px-2 py-1 text-[10px] font-semibold">
      {labels[status] || status}
    </span>
  );
}
