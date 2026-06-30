/**
 * Serviço de pacientes.
 * Encapsula todas as chamadas de API relacionadas a pacientes.
 */

import { api } from "@/lib/api";
import type {
  Patient,
  CreatePatientPayload,
  PaginatedResponse,
} from "@/types";

export interface PatientFilters {
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export const patientsService = {
  /**
   * Lista todos os pacientes com filtros opcionais e paginação.
   */
  list: async (filters?: PatientFilters): Promise<PaginatedResponse<Patient>> => {
    const params = new URLSearchParams();
    if (filters?.search) params.set("search", filters.search);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.page) params.set("page", String(filters.page));
    if (filters?.page_size) params.set("page_size", String(filters.page_size));

    const response = await api.get<PaginatedResponse<Patient>>(
      `patients/?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Busca todos os campos administrativos editáveis de um paciente.
   * O endpoint dedicado evita preencher campos ausentes com valores padrão
   * e sobrescrevê-los acidentalmente durante um PATCH.
   */
  getById: async (id: number): Promise<Patient> => {
    const response = await api.get<Patient>(`patients/${id}/form/`);
    return response.data;
  },

  /**
   * Cria um novo paciente.
   */
  create: async (data: CreatePatientPayload): Promise<Patient> => {
    const response = await api.post<Patient>("patients/", data);
    return response.data;
  },

  /**
   * Atualiza um paciente existente.
   */
  update: async (
    id: number,
    data: Partial<CreatePatientPayload>
  ): Promise<Patient> => {
    const response = await api.patch<Patient>(`patients/${id}/`, data);
    return response.data;
  },

  /**
   * Realiza soft-delete de um paciente.
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`patients/${id}/`);
  },
};
