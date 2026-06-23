/**
 * Serviço de prontuários (records).
 * Encapsula todas as chamadas de API relacionadas a registros clínicos.
 */

import { api } from "@/lib/api";
import type { ClinicalRecord, CreateRecordPayload, PaginatedResponse } from "@/types";

export interface RecordFilters {
  patient?: number;
  appointment?: number;
  page?: number;
}

export const recordsService = {
  /**
   * Lista prontuários com filtros opcionais.
   */
  list: async (filters?: RecordFilters): Promise<PaginatedResponse<ClinicalRecord>> => {
    const params = new URLSearchParams();
    if (filters?.patient) params.set("patient", String(filters.patient));
    if (filters?.appointment) params.set("appointment", String(filters.appointment));
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<PaginatedResponse<ClinicalRecord>>(
      `records/?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Busca um prontuário pelo ID.
   */
  getById: async (id: number): Promise<ClinicalRecord> => {
    const response = await api.get<ClinicalRecord>(`records/${id}/`);
    return response.data;
  },

  /**
   * Cria um novo prontuário.
   */
  create: async (data: CreateRecordPayload): Promise<ClinicalRecord> => {
    const response = await api.post<ClinicalRecord>("records/", data);
    return response.data;
  },

  /**
   * Atualiza um prontuário (somente se não estiver bloqueado – regra das 48h).
   */
  update: async (
    id: number,
    data: Partial<CreateRecordPayload>
  ): Promise<ClinicalRecord> => {
    const response = await api.patch<ClinicalRecord>(`records/${id}/`, data);
    return response.data;
  },

  /**
   * Deleta um prontuário (somente se não estiver bloqueado).
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`records/${id}/`);
  },
};
