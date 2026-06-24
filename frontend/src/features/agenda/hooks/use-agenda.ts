/**
 * Hooks TanStack Query para agenda.
 * Centraliza fetching, caching e mutações de agendamentos.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { agendaService, type AppointmentFilters } from "../services/agenda.service";
import { QUERY_KEYS } from "@/constants";
import type { CreateAppointmentPayload } from "@/types";

/**
 * Hook para listar agendamentos com filtros opcionais.
 */
export function useAppointments(filters?: AppointmentFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.appointments, filters],
    queryFn: () => agendaService.list(filters),
  });
}

/**
 * Hook para buscar consultas de hoje.
 */
export function useTodayAppointments() {
  return useQuery({
    queryKey: [...QUERY_KEYS.appointments, "today"],
    queryFn: () => agendaService.today(),
  });
}

/**
 * Hook para buscar um agendamento específico.
 */
export function useAppointment(id: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.appointment(id!),
    queryFn: () => agendaService.getById(id!),
    enabled: !!id,
  });
}

/**
 * Hook para criar um novo agendamento.
 */
export function useCreateAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => agendaService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointments });
      toast.success("Consulta agendada com sucesso.");
    },
    onError: (error: any) => {
      const serverMsg = error.response?.data?.start_time?.[0] || error.response?.data?.detail;
      toast.error("Erro ao agendar consulta.", {
        description: serverMsg || "Verifique conflitos de horário com o terapeuta.",
      });
    },
  });
}

/**
 * Hook para atualizar um agendamento.
 */
export function useUpdateAppointment(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreateAppointmentPayload>) =>
      agendaService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointments });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointment(id) });
      toast.success("Consulta atualizada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao atualizar consulta.");
    },
  });
}

/**
 * Hook para atualizar o status de um agendamento.
 */
export function useUpdateAppointmentStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      status,
      cancellationReason,
    }: {
      id: number;
      status: string;
      cancellationReason?: string;
    }) => agendaService.updateStatus(id, status, cancellationReason),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointments });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointment(variables.id) });
      toast.success("Status do agendamento atualizado.");
    },
    onError: (error: any) => {
      const serverMsg = error.response?.data?.status?.[0] || error.response?.data?.detail;
      toast.error("Erro ao atualizar status.", {
        description: serverMsg || "Não foi possível mudar o status desta consulta.",
      });
    },
  });
}

/**
 * Hook para buscar slots livres disponíveis.
 */
export function useAvailableSlots(date: string, duration: number, enabled: boolean) {
  return useQuery({
    queryKey: ["appointments", "availability", date, duration],
    queryFn: () => agendaService.checkAvailability(date, duration),
    enabled: enabled && !!date && !!duration,
    staleTime: 5000, // cache curto para disponibilidade
  });
}

/**
 * Hook para cancelar um agendamento.
 */
export function useDeleteAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => agendaService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointments });
      toast.success("Consulta cancelada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao cancelar consulta.");
    },
  });
}
