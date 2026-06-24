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
  transaction_type?: "income" | "expense";
  payment_status?: string;
  category?: string;
  patient?: string;
  page?: number;
}

export interface FinancialSummary {
  year: number;
  month: number;
  total_income: string;
  total_expense: string;
  balance: string;
  total_pending: string;
  transaction_count: number;
}

export const financeiroService = {
  /**
   * Lista transações com filtros opcionais.
   */
  list: async (
    filters?: TransactionFilters
  ): Promise<FinancialTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.transaction_type) params.set("transaction_type", filters.transaction_type);
    if (filters?.payment_status) params.set("payment_status", filters.payment_status);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.patient) params.set("patient", filters.patient);
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<FinancialTransaction[] | PaginatedResponse<FinancialTransaction>>(
      `financeiro/?${params.toString()}`
    );
    return Array.isArray(response.data) ? response.data : response.data.results || [];
  },

  /**
   * Busca uma transação pelo ID.
   */
  getById: async (id: number): Promise<FinancialTransaction> => {
    const response = await api.get<FinancialTransaction>(`financeiro/${id}/`);
    return response.data;
  },

  /**
   * Busca o resumo financeiro mensal.
   */
  getSummary: async (year: number, month: number): Promise<FinancialSummary> => {
    const response = await api.get<FinancialSummary>("financeiro/summary/", {
      params: { year, month },
    });
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
    paymentMethod: string = "pix",
    paidAt?: string
  ): Promise<FinancialTransaction> => {
    const response = await api.patch<FinancialTransaction>(`financeiro/${id}/pay/`, {
      payment_method: paymentMethod,
      paid_at: paidAt ?? new Date().toISOString(),
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
