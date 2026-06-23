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
 * Hook para buscar agendamentos de um dia específico.
 */
export function useAppointmentsByDate(date: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.appointmentsByDate(date!),
    queryFn: () => agendaService.list({ date: date! }),
    enabled: !!date,
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
    mutationFn: (data: CreateAppointmentPayload) => agendaService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.appointments });
      toast.success("Consulta agendada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao agendar consulta. Verifique conflitos de horário.");
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
