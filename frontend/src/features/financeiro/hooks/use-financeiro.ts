/**
 * Hooks TanStack Query para o módulo financeiro.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  financeiroService,
  type TransactionFilters,
} from "../services/financeiro.service";
import { QUERY_KEYS } from "@/constants";
import type { CreateTransactionPayload } from "@/types";

/**
 * Hook para listar transações financeiras com filtros.
 */
export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.transactions, filters],
    queryFn: () => financeiroService.list(filters),
  });
}

/**
 * Hook para buscar o resumo financeiro do período.
 */
export function useFinancialSummary(filters?: {
  date_from?: string;
  date_to?: string;
}) {
  return useQuery({
    queryKey: [...QUERY_KEYS.transactionsSummary, filters],
    queryFn: () => financeiroService.getSummary(filters),
  });
}

/**
 * Hook para criar uma nova transação.
 */
export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTransactionPayload) =>
      financeiroService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transactions });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.transactionsSummary,
      });
      toast.success("Transação registrada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao registrar transação. Tente novamente.");
    },
  });
}

/**
 * Hook para marcar uma transação como paga (1 clique).
 */
export function useMarkAsPaid() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, paymentDate }: { id: number; paymentDate?: string }) =>
      financeiroService.markAsPaid(id, paymentDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transactions });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.transactionsSummary,
      });
      toast.success("Pagamento registrado com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao registrar pagamento.");
    },
  });
}

/**
 * Hook para atualizar uma transação.
 */
export function useUpdateTransaction(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<CreateTransactionPayload>) =>
      financeiroService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transactions });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transaction(id) });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.transactionsSummary,
      });
      toast.success("Transação atualizada com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao atualizar transação.");
    },
  });
}

/**
 * Hook para deletar uma transação.
 */
export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => financeiroService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.transactions });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.transactionsSummary,
      });
      toast.success("Transação removida com sucesso.");
    },
    onError: () => {
      toast.error("Erro ao remover transação.");
    },
  });
}
