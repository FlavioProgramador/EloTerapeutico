/**
 * Hooks TanStack Query para pacientes.
 * Centraliza fetching, caching e mutações de dados de pacientes.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { patientsService, type PatientFilters } from "../services/patients.service";
import { QUERY_KEYS } from "@/constants";
import type { CreatePatientPayload } from "@/types";

/**
 * Hook para listar pacientes com filtros opcionais.
 * Os dados são cacheados por 60s e refetchados automaticamente.
 */
export function usePatients(filters?: PatientFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.patients, filters],
    queryFn: () => patientsService.list(filters),
  });
}

/**
 * Hook para buscar um paciente específico por ID.
 * Só executa a query se o ID for fornecido.
 */
export function usePatient(id: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.patient(id!),
    queryFn: () => patientsService.getById(id!),
    enabled: !!id,
  });
}

/**
 * Hook para criar um novo paciente.
 * Invalida a lista de pacientes após sucesso.
 */
export function useCreatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreatePatientPayload) => patientsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients });
      toast.success("Paciente cadastrado com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao cadastrar paciente. Tente novamente.");
    },
  });
}

/**
 * Hook para atualizar um paciente existente.
 */
export function useUpdatePatient(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreatePatientPayload>) =>
      patientsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patient(id) });
      toast.success("Paciente atualizado com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao atualizar paciente. Tente novamente.");
    },
  });
}

/**
 * Hook para deletar (soft-delete) um paciente.
 */
export function useDeletePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => patientsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients });
      toast.success("Paciente removido com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao remover paciente. Tente novamente.");
    },
  });
}
