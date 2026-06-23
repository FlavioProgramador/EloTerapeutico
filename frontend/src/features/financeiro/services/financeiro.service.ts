/**
 * Serviço financeiro.
 * Encapsula todas as chamadas de API relacionadas a transações financeiras.
 */

import { api } from "@/lib/api";
import type {
  FinancialTransaction,
  CreateTransactionPayload,
  PaginatedResponse,
} from "@/types";

export interface TransactionFilters {
  type?: "income" | "expense";
  status?: string;
  patient?: number;
  date_from?: string;
  date_to?: string;
  page?: number;
}

export interface FinancialSummary {
  total_income: string;
  total_expense: string;
  balance: string;
  pending_count: number;
  overdue_count: number;
}

export const financeiroService = {
  /**
   * Lista transações com filtros opcionais.
   */
  list: async (
    filters?: TransactionFilters
  ): Promise<PaginatedResponse<FinancialTransaction>> => {
    const params = new URLSearchParams();
    if (filters?.type) params.set("type", filters.type);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.patient) params.set("patient", String(filters.patient));
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<PaginatedResponse<FinancialTransaction>>(
      `financeiro/?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Busca uma transação pelo ID.
   */
  getById: async (id: number): Promise<FinancialTransaction> => {
    const response = await api.get<FinancialTransaction>(`financeiro/${id}/`);
    return response.data;
  },

  /**
   * Busca o resumo financeiro (total receitas, despesas, saldo).
   */
  getSummary: async (filters?: {
    date_from?: string;
    date_to?: string;
  }): Promise<FinancialSummary> => {
    const params = new URLSearchParams();
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);

    const response = await api.get<FinancialSummary>(
      `financeiro/summary/?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Cria uma nova transação financeira.
   */
  create: async (
    data: CreateTransactionPayload
  ): Promise<FinancialTransaction> => {
    const response = await api.post<FinancialTransaction>("financeiro/", data);
    return response.data;
  },

  /**
   * Atualiza uma transação existente.
   */
  update: async (
    id: number,
    data: Partial<CreateTransactionPayload>
  ): Promise<FinancialTransaction> => {
    const response = await api.patch<FinancialTransaction>(
      `financeiro/${id}/`,
      data
    );
    return response.data;
  },

  /**
   * Marca uma transação como paga (1 clique).
   */
  markAsPaid: async (
    id: number,
    paymentDate?: string
  ): Promise<FinancialTransaction> => {
    const response = await api.patch<FinancialTransaction>(`financeiro/${id}/`, {
      status: "paid",
      payment_date:
        paymentDate ?? new Date().toISOString().split("T")[0],
    });
    return response.data;
  },

  /**
   * Deleta uma transação.
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`financeiro/${id}/`);
  },
};
