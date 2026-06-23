/**
 * Serviço de agenda (appointments).
 * Encapsula todas as chamadas de API relacionadas a agendamentos.
 */

import { api } from "@/lib/api";
import type {
  Appointment,
  CreateAppointmentPayload,
  PaginatedResponse,
} from "@/types";

export interface AppointmentFilters {
  date?: string;
  date_from?: string;
  date_to?: string;
  patient?: number;
  status?: string;
  page?: number;
}

export const agendaService = {
  /**
   * Lista agendamentos com filtros opcionais.
   */
  list: async (
    filters?: AppointmentFilters
  ): Promise<PaginatedResponse<Appointment>> => {
    const params = new URLSearchParams();
    if (filters?.date) params.set("date", filters.date);
    if (filters?.date_from) params.set("date_from", filters.date_from);
    if (filters?.date_to) params.set("date_to", filters.date_to);
    if (filters?.patient) params.set("patient", String(filters.patient));
    if (filters?.status) params.set("status", filters.status);
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<PaginatedResponse<Appointment>>(
      `agenda/?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Busca um agendamento pelo ID.
   */
  getById: async (id: number): Promise<Appointment> => {
    const response = await api.get<Appointment>(`agenda/${id}/`);
    return response.data;
  },

  /**
   * Cria um novo agendamento.
   */
  create: async (data: CreateAppointmentPayload): Promise<Appointment> => {
    const response = await api.post<Appointment>("agenda/", data);
    return response.data;
  },

  /**
   * Atualiza um agendamento existente.
   */
  update: async (
    id: number,
    data: Partial<CreateAppointmentPayload>
  ): Promise<Appointment> => {
    const response = await api.patch<Appointment>(`agenda/${id}/`, data);
    return response.data;
  },

  /**
   * Cancela (deleta) um agendamento.
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`agenda/${id}/`);
  },
};
