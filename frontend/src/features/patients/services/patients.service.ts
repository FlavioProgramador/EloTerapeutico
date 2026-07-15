/** Serviço tipado para os fluxos administrativos de pacientes. */

import { api } from "@/lib/api";
import type { PaginatedResponse, Patient } from "@/types";
import type {
  PatientFormRecord,
  PatientFormRequest,
  PatientProfessionalOption,
} from "../types/patient-form.types";

export interface PatientFilters {
  search?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

type PatientFormResponse = PatientFormRecord & { created_at: string };

export const patientsService = {
  list: async (
    filters?: PatientFilters,
  ): Promise<PaginatedResponse<Patient>> => {
    const params = new URLSearchParams();
    if (filters?.search) params.set("search", filters.search);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.page) params.set("page", String(filters.page));
    if (filters?.page_size) params.set("page_size", String(filters.page_size));
    const response = await api.get<PaginatedResponse<Patient>>(
      `patients/?${params.toString()}`,
    );
    return response.data;
  },

  getById: async (id: number): Promise<PatientFormResponse> => {
    const response = await api.get<PatientFormResponse>(`patients/${id}/form/`);
    return response.data;
  },

  create: async (
    data: PatientFormRequest | FormData,
  ): Promise<PatientFormResponse> => {
    const response = await api.post<PatientFormResponse>("patients/", data);
    return response.data;
  },

  update: async (
    id: number,
    data: PatientFormRequest | FormData,
  ): Promise<PatientFormResponse> => {
    const response = await api.patch<PatientFormResponse>(
      `patients/${id}/`,
      data,
    );
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`patients/${id}/`);
  },

  deactivate: async (id: number): Promise<void> => {
    await api.post(`patients/${id}/deactivate/`);
  },

  restore: async (id: number): Promise<void> => {
    await api.post(`patients/${id}/restore/`);
  },

  professionals: async (): Promise<PatientProfessionalOption[]> => {
    const response = await api.get<PatientProfessionalOption[]>(
      "patients/professionals/",
    );
    return response.data;
  },

  createRegistrationLink: async (
    id: number,
  ): Promise<{ path: string; expires_at: string }> => {
    const response = await api.post<{ path: string; expires_at: string }>(
      `patients/${id}/registration-link/`,
    );
    return response.data;
  },
};
