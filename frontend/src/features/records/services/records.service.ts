/**
 * Serviço de prontuários (records/evolutions).
 * Encapsula todas as chamadas de API relacionadas a registros clínicos e anamnese.
 */

import { api } from "@/lib/api";
import type {
  EvolutionListItem,
  EvolutionDetail,
  CreateEvolutionPayload,
  Anamnesis,
  Addendum,
  CreateAddendumPayload,
} from "@/types";

export interface RecordFilters {
  patient?: number;
  appointment?: number;
  page?: number;
}

export const recordsService = {
  /**
   * Lista evoluções com filtros opcionais.
   */
  list: async (filters?: RecordFilters): Promise<EvolutionListItem[]> => {
    const params = new URLSearchParams();
    if (filters?.patient) params.set("patient", String(filters.patient));
    if (filters?.appointment)
      params.set("appointment", String(filters.appointment));
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<
      EvolutionListItem[] | { results: EvolutionListItem[] }
    >(`records/evolutions/?${params.toString()}`);
    return Array.isArray(response.data)
      ? response.data
      : response.data.results || [];
  },

  /**
   * Busca os detalhes de uma evolução pelo ID (incluindo conteúdo clínico).
   */
  getById: async (id: number): Promise<EvolutionDetail> => {
    const response = await api.get<EvolutionDetail>(
      `records/evolutions/${id}/`,
    );
    return response.data;
  },

  /**
   * Cria uma nova evolução clínica.
   */
  create: async (data: CreateEvolutionPayload): Promise<EvolutionDetail> => {
    const response = await api.post<EvolutionDetail>(
      "records/evolutions/",
      data,
    );
    return response.data;
  },

  /**
   * Atualiza uma evolução existente (se não bloqueada).
   */
  update: async (
    id: number,
    data: Partial<CreateEvolutionPayload>,
  ): Promise<EvolutionDetail> => {
    const response = await api.patch<EvolutionDetail>(
      `records/evolutions/${id}/`,
      data,
    );
    return response.data;
  },

  /**
   * Busca a anamnese inicial de um paciente.
   */
  getAnamnesis: async (patientId: number): Promise<Anamnesis | null> => {
    try {
      const response = await api.get<Anamnesis>(
        `records/patients/${patientId}/anamnesis/`,
      );
      return response.data;
    } catch (error) {
      const err = error as { response?: { status?: number } };
      if (err.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Salva (cria ou atualiza) a anamnese de um paciente.
   */
  saveAnamnesis: async (
    patientId: number,
    data: Anamnesis,
    exists: boolean,
  ): Promise<Anamnesis> => {
    if (exists) {
      const response = await api.put<Anamnesis>(
        `records/patients/${patientId}/anamnesis/`,
        data,
      );
      return response.data;
    } else {
      const response = await api.post<Anamnesis>(
        `records/patients/${patientId}/anamnesis/`,
        data,
      );
      return response.data;
    }
  },

  /**
   * Adiciona um aditivo a uma evolução bloqueada.
   */
  createAddendum: async (
    evolutionId: number,
    data: CreateAddendumPayload,
  ): Promise<Addendum> => {
    const response = await api.post<Addendum>(
      `records/evolutions/${evolutionId}/addendum/`,
      data,
    );
    return response.data;
  },
};
