/**
 * Serviço financeiro.
 * Encapsula todas as chamadas de API relacionadas a transações financeiras.
 */

import { api } from "@/lib/api";
import type {
  FinancialTransaction,
  CreateTransactionPayload,
  PaginatedResponse,
  FinancialPaymentMethod,
  TransactionStatus,
  TransactionType,
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

type ApiTransactionStatus = Exclude<TransactionStatus, "overdue">;

interface FinancialTransactionApi {
  id: number;
  patient?: number | null;
  appointment?: number | null;
  patient_name?: string | null;
  transaction_type: TransactionType;
  category: FinancialTransaction["category"];
  amount: string;
  payment_method?: FinancialPaymentMethod;
  payment_status: ApiTransactionStatus;
  due_date?: string | null;
  paid_at?: string | null;
  description?: string;
  receipt_url?: string;
  is_overdue?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface TransactionApiPayload {
  patient?: number;
  appointment?: number;
  transaction_type: TransactionType;
  category: FinancialTransaction["category"];
  amount: string | number;
  payment_method?: FinancialPaymentMethod;
  payment_status?: ApiTransactionStatus;
  due_date: string;
  paid_at?: string;
  description: string;
}

function toPaymentDate(paidAt?: string | null): string | undefined {
  return paidAt ? paidAt.split("T")[0] : undefined;
}

function toPaidAt(paymentDate?: string): string | undefined {
  if (!paymentDate) return undefined;
  return new Date(`${paymentDate}T12:00:00`).toISOString();
}

function toAppTransaction(data: FinancialTransactionApi): FinancialTransaction {
  return {
    id: data.id,
    patient: data.patient ?? undefined,
    patient_name: data.patient_name ?? undefined,
    appointment: data.appointment ?? undefined,
    description: data.description ?? "",
    amount: data.amount,
    type: data.transaction_type,
    category: data.category,
    status:
      data.payment_status === "pending" && data.is_overdue
        ? "overdue"
        : data.payment_status,
    due_date: data.due_date ?? "",
    payment_date: toPaymentDate(data.paid_at),
    payment_method: data.payment_method,
    is_overdue: data.is_overdue,
    created_at: data.created_at ?? "",
    updated_at: data.updated_at ?? "",
  };
}

function normalizePaymentStatus(
  status: CreateTransactionPayload["status"],
): ApiTransactionStatus | undefined {
  return status === "overdue" ? "pending" : status;
}

function toApiPayload(data: CreateTransactionPayload): TransactionApiPayload {
  const paymentStatus = normalizePaymentStatus(data.status);

  return {
    patient: data.patient,
    appointment: data.appointment,
    transaction_type: data.type,
    category: data.category,
    amount: data.amount,
    payment_method: data.payment_method,
    payment_status: paymentStatus,
    due_date: data.due_date,
    paid_at: paymentStatus === "paid" ? toPaidAt(data.payment_date) : undefined,
    description: data.description,
  };
}

function toApiPatchPayload(
  data: Partial<CreateTransactionPayload>,
): Partial<TransactionApiPayload> {
  const paymentStatus = normalizePaymentStatus(data.status);

  return {
    patient: data.patient,
    appointment: data.appointment,
    transaction_type: data.type,
    category: data.category,
    amount: data.amount,
    payment_method: data.payment_method,
    payment_status: paymentStatus,
    due_date: data.due_date,
    paid_at: paymentStatus === "paid" ? toPaidAt(data.payment_date) : undefined,
    description: data.description,
  };
}

export const financeiroService = {
  /**
   * Lista transações com filtros opcionais.
   */
  list: async (
    filters?: TransactionFilters,
  ): Promise<FinancialTransaction[]> => {
    const params = new URLSearchParams();
    if (filters?.transaction_type)
      params.set("transaction_type", filters.transaction_type);
    if (filters?.payment_status)
      params.set("payment_status", filters.payment_status);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.patient) params.set("patient", filters.patient);
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<
      FinancialTransactionApi[] | PaginatedResponse<FinancialTransactionApi>
    >(`financeiro/?${params.toString()}`);
    const results = Array.isArray(response.data)
      ? response.data
      : response.data.results || [];
    return results.map(toAppTransaction);
  },

  /**
   * Busca uma transação pelo ID.
   */
  getById: async (id: number): Promise<FinancialTransaction> => {
    const response = await api.get<FinancialTransactionApi>(
      `financeiro/${id}/`,
    );
    return toAppTransaction(response.data);
  },

  /**
   * Busca o resumo financeiro mensal.
   */
  getSummary: async (
    year: number,
    month: number,
  ): Promise<FinancialSummary> => {
    const response = await api.get<FinancialSummary>("financeiro/summary/", {
      params: { year, month },
    });
    return response.data;
  },

  /**
   * Cria uma nova transação financeira.
   */
  create: async (
    data: CreateTransactionPayload,
  ): Promise<FinancialTransaction> => {
    const response = await api.post<FinancialTransactionApi>(
      "financeiro/",
      toApiPayload(data),
    );
    return toAppTransaction(response.data);
  },

  /**
   * Atualiza uma transação existente.
   */
  update: async (
    id: number,
    data: Partial<CreateTransactionPayload>,
  ): Promise<FinancialTransaction> => {
    const response = await api.patch<FinancialTransactionApi>(
      `financeiro/${id}/`,
      toApiPatchPayload(data),
    );
    return toAppTransaction(response.data);
  },

  /**
   * Marca uma transação como paga (1 clique).
   */
  markAsPaid: async (
    id: number,
    paymentMethod: FinancialPaymentMethod = "pix",
    paidAt?: string,
  ): Promise<FinancialTransaction> => {
    const response = await api.patch<FinancialTransactionApi>(
      `financeiro/${id}/pay/`,
      {
        payment_method: paymentMethod,
        paid_at: paidAt ?? new Date().toISOString(),
      },
    );
    return toAppTransaction(response.data);
  },

  /**
   * Deleta uma transação.
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`financeiro/${id}/`);
  },

  /**
   * Cancela uma transação pendente.
   */
  cancel: async (id: number): Promise<FinancialTransaction> => {
    const response = await api.post<FinancialTransactionApi>(
      `financeiro/${id}/cancel/`,
    );
    return toAppTransaction(response.data);
  },

  /**
   * Estorna uma transação paga.
   */
  refund: async (id: number): Promise<FinancialTransaction> => {
    const response = await api.post<FinancialTransactionApi>(
      `financeiro/${id}/refund/`,
    );
    return toAppTransaction(response.data);
  },

  /**
   * Exporta a lista de transações filtrada em formato CSV.
   */
  exportCSV: async (filters?: TransactionFilters): Promise<Blob> => {
    const params = new URLSearchParams();
    if (filters?.transaction_type)
      params.set("transaction_type", filters.transaction_type);
    if (filters?.payment_status)
      params.set("payment_status", filters.payment_status);
    if (filters?.category) params.set("category", filters.category);
    if (filters?.patient) params.set("patient", filters.patient);

    const response = await api.get(`financeiro/export/?${params.toString()}`, {
      responseType: "blob",
    });
    return response.data as unknown as Blob;
  },

  /**
   * Obtém a lista de consultas concluídas sem lançamento financeiro associado.
   */
  getUnbilledAppointments: async (): Promise<
    Array<{
      id: number;
      patient_id: number;
      patient_name: string;
      start_time: string;
      end_time: string;
      session_value: string;
    }>
  > => {
    const response = await api.get<
      Array<{
        id: number;
        patient_id: number;
        patient_name: string;
        start_time: string;
        end_time: string;
        session_value: string;
      }>
    >("financeiro/unbilled-appointments/");
    return response.data;
  },
};
