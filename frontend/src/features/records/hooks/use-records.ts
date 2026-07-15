/**
 * Hooks TanStack Query para prontuários clínicos.
 * Centraliza fetching, caching e mutações de evoluções, anamnese e aditivos.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  recordsService,
  type RecordFilters,
} from "../services/records.service";
import { QUERY_KEYS } from "@/constants";
import type {
  CreateEvolutionPayload,
  Anamnesis,
  CreateAddendumPayload,
} from "@/types";

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
 * Hook para buscar os detalhes de uma evolução específica.
 */
export function useRecord(id: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.record(id!),
    queryFn: () => recordsService.getById(id!),
    enabled: !!id,
  });
}

/**
 * Hook para criar uma nova evolução clínica.
 */
export function useCreateRecord() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateEvolutionPayload) => recordsService.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      if (variables.patient) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.recordsByPatient(variables.patient),
        });
      }
      toast.success("Evolução clínica registrada com sucesso.");
    },
    onError: (error: unknown) => {
      let serverMsg = "";
      if (error && typeof error === "object" && "response" in error) {
        const errObj = (
          error as {
            response?: { data?: { session_date?: string[]; detail?: string } };
          }
        ).response?.data;
        serverMsg = errObj?.session_date?.[0] || errObj?.detail || "";
      }
      toast.error("Erro ao salvar evolução clínica.", {
        description:
          serverMsg || "Verifique se já existe um registro para esta data.",
      });
    },
  });
}

/**
 * Hook para atualizar uma evolução clínica (se não bloqueada).
 */
export function useUpdateRecord(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreateEvolutionPayload>) =>
      recordsService.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.records });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.record(id) });
      if (data.patient) {
        queryClient.invalidateQueries({
          queryKey: QUERY_KEYS.recordsByPatient(data.patient),
        });
      }
      toast.success("Evolução clínica atualizada com sucesso.");
    },
    onError: (error: unknown) => {
      let isLocked = false;
      let detail = "Erro ao atualizar evolução clínica.";
      if (error && typeof error === "object" && "response" in error) {
        const response = (
          error as {
            response?: { status?: number; data?: { detail?: string } };
          }
        ).response;
        isLocked = response?.status === 403 || response?.status === 400;
        detail = response?.data?.detail || detail;
      }
      toast.error(
        isLocked
          ? "Esta evolução está bloqueada para edição (prazo de 48h esgotado)."
          : "Erro ao atualizar evolução.",
        { description: detail },
      );
    },
  });
}

/**
 * Hook para buscar a anamnese de um paciente.
 */
export function useAnamnesis(patientId: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.anamnesis(patientId!),
    queryFn: () => recordsService.getAnamnesis(patientId!),
    enabled: !!patientId,
  });
}

/**
 * Hook para salvar (criar ou atualizar) a anamnese de um paciente.
 */
export function useSaveAnamnesis(patientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ data, exists }: { data: Anamnesis; exists: boolean }) =>
      recordsService.saveAnamnesis(patientId, data, exists),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.anamnesis(patientId),
      });
      toast.success("Ficha de anamnese salva com sucesso.");
    },
    onError: (error: unknown) => {
      let serverMsg = "Erro ao salvar anamnese.";
      if (error && typeof error === "object" && "response" in error) {
        serverMsg =
          (error as { response?: { data?: { detail?: string } } }).response
            ?.data?.detail || serverMsg;
      }
      toast.error("Erro ao salvar.", { description: serverMsg });
    },
  });
}

/**
 * Hook para adicionar um aditivo a uma evolução bloqueada.
 */
export function useCreateAddendum(evolutionId: number, patientId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAddendumPayload) =>
      recordsService.createAddendum(evolutionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.record(evolutionId),
      });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.recordsByPatient(patientId),
      });
      toast.success("Aditivo inserido com sucesso.");
    },
    onError: (error: unknown) => {
      let serverMsg = "Erro ao registrar aditivo.";
      if (error && typeof error === "object" && "response" in error) {
        serverMsg =
          (error as { response?: { data?: { detail?: string } } }).response
            ?.data?.detail || serverMsg;
      }
      toast.error("Erro ao salvar aditivo.", { description: serverMsg });
    },
  });
}
