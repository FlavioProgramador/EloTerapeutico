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
  start_time_gte?: string;
  start_time_lte?: string;
  patient?: number;
  status?: string;
  page?: number;
}

export interface TimeSlot {
  start: string;
  end: string;
  start_datetime: string;
  end_datetime: string;
}

export const agendaService = {
  /**
   * Lista agendamentos com filtros opcionais.
   */
  list: async (
    filters?: AppointmentFilters
  ): Promise<Appointment[]> => {
    const params = new URLSearchParams();
    if (filters?.date) params.set("date", filters.date);
    if (filters?.start_time_gte) params.set("start_time_gte", filters.start_time_gte);
    if (filters?.start_time_lte) params.set("start_time_lte", filters.start_time_lte);
    if (filters?.patient) params.set("patient", String(filters.patient));
    if (filters?.status) params.set("status", filters.status);
    if (filters?.page) params.set("page", String(filters.page));

    const response = await api.get<Appointment[] | PaginatedResponse<Appointment>>(
      `agenda/appointments/?${params.toString()}`
    );
    return Array.isArray(response.data) ? response.data : response.data.results || [];
  },

  /**
   * Busca as consultas de hoje.
   */
  today: async (): Promise<Appointment[]> => {
    const response = await api.get<Appointment[]>("agenda/appointments/today/");
    return response.data;
  },

  /**
   * Busca um agendamento pelo ID.
   */
  getById: async (id: number): Promise<Appointment> => {
    const response = await api.get<Appointment>(`agenda/appointments/${id}/`);
    return response.data;
  },

  /**
   * Cria um novo agendamento.
   */
  create: async (data: CreateAppointmentPayload): Promise<Appointment> => {
    const response = await api.post<Appointment>("agenda/appointments/", data);
    return response.data;
  },

  /**
   * Atualiza um agendamento existente.
   */
  update: async (
    id: number,
    data: Partial<CreateAppointmentPayload>
  ): Promise<Appointment> => {
    const response = await api.patch<Appointment>(`agenda/appointments/${id}/`, data);
    return response.data;
  },

  /**
   * Atualiza o status de um agendamento.
   */
  updateStatus: async (
    id: number,
    status: string,
    cancellationReason?: string
  ): Promise<Appointment> => {
    const response = await api.patch<Appointment>(`agenda/appointments/${id}/status/`, {
      status,
      cancellation_reason: cancellationReason,
    });
    return response.data;
  },

  /**
   * Verifica slots de horários livres disponíveis.
   */
  checkAvailability: async (date: string, duration: number): Promise<TimeSlot[]> => {
    const response = await api.post<TimeSlot[]>("agenda/appointments/check-availability/", {
      date,
      duration,
    });
    return response.data;
  },

  /**
   * Cancela/deleta um agendamento.
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`agenda/appointments/${id}/`);
  },
};
