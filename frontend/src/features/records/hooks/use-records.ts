/**
 * Hooks TanStack Query para prontuários clínicos.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { recordsService, type RecordFilters } from "../services/records.service";
import { QUERY_KEYS } from "@/constants";
import type { CreateRecordPayload } from "@/types";

/**
 * Hook para listar prontuários com filtros opcionais.
 */
export function useRecords(filters?: RecordFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.records, filters],
    queryFn: () => recordsService.list(filters),
  });
}

/**
 * Hook para buscar prontuários de um paciente específico.
 */
export function useRecordsByPatient(patientId: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.recordsByPatient(patientId!),
    queryFn: () => recordsService.list({ patient: patientId! }),
    enabled: !!patientId,
  });
}

/**
 * Hook para buscar um prontuário específico.
 */
export function useRecord(id: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.record(id!),
    queryFn: () => recordsService.getById(id!),
    enabled: !!id,
  });
}

/**
 * Hook para criar um novo prontuário.
 */
export function useCreateRecord() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateRecordPayload) => recordsService.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      if (variables.patient) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.recordsByPatient(variables.patient),
        });
      }
      toast.success("Evolução registrada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao salvar evolução. Tente novamente.");
    },
  });
}

/**
 * Hook para atualizar um prontuário (se não bloqueado).
 */
export function useUpdateRecord(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreateRecordPayload>) =>
      recordsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.record(id) });
      toast.success("Evolução atualizada com sucesso.");
    },
    onError: (error: any) => {
      // Mensagem específica para tentativas de edição após 48h
      const isLocked = error?.response?.status === 403;
      toast.error(
        isLocked
          ? "Esta evolução está bloqueada para edição (prazo de 48h esgotado)."
          : "Erro ao atualizar evolução."
      );
    },
  });
}

/**
 * Hook para deletar um prontuário.
 */
export function useDeleteRecord() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => recordsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      toast.success("Evolução removida com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao remover evolução.");
    },
  });
}
