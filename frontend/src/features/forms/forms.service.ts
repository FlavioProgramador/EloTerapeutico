import { api } from "@/lib/api";

import type {
  FormFilters,
  FormPayload,
  FormTemplate,
  PaginatedForms,
  TherapeuticForm,
} from "./types";

function cleanParams(filters?: FormFilters) {
  const params = new URLSearchParams();
  Object.entries(filters ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "")
      params.set(key, String(value));
  });
  return params;
}

export const formsService = {
  list: async (filters?: FormFilters) => {
    const response = await api.get<PaginatedForms<TherapeuticForm>>("forms/", {
      params: cleanParams(filters),
    });
    return response.data;
  },
  get: async (id: number) => {
    const response = await api.get<TherapeuticForm>(`forms/${id}/`);
    return response.data;
  },
  create: async (payload: FormPayload) => {
    const response = await api.post<TherapeuticForm>("forms/", payload);
    return response.data;
  },
  update: async (id: number, payload: Partial<FormPayload>) => {
    const response = await api.patch<TherapeuticForm>(`forms/${id}/`, payload);
    return response.data;
  },
  remove: async (id: number) => {
    await api.delete(`forms/${id}/`);
  },
  duplicate: async (id: number) => {
    const response = await api.post<TherapeuticForm>(`forms/${id}/duplicate/`);
    return response.data;
  },
  archive: async (id: number) => {
    const response = await api.post<TherapeuticForm>(`forms/${id}/archive/`);
    return response.data;
  },
  restore: async (id: number) => {
    const response = await api.post<TherapeuticForm>(`forms/${id}/restore/`);
    return response.data;
  },
  templates: async (filters?: FormFilters) => {
    const response = await api.get<PaginatedForms<FormTemplate>>(
      "forms/templates/",
      { params: cleanParams(filters) },
    );
    return response.data;
  },
  createFromTemplate: async (templateId: number, payload: FormPayload) => {
    const response = await api.post<TherapeuticForm>(
      `forms/from-template/${templateId}/`,
      payload,
    );
    return response.data;
  },
};
