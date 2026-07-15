import { api } from "@/lib/api";
import type { Appointment as LegacyAppointment } from "@/types";
import type {
  AgendaAppointment,
  AgendaRoom,
  AppointmentFilters,
  AppointmentRecurrence,
  CreateAppointmentPayload,
  CreatePackagePayload,
  CreateScheduleBlockPayload,
  PaginatedAgendaResponse,
  PatientPackage,
  ScheduleBlock,
  TelemedicineRoom,
  TimeSlot,
} from "../types";

function buildParams(filters?: Record<string, unknown>) {
  const params = new URLSearchParams();
  Object.entries(filters || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    params.set(key, String(value));
  });
  return params.toString();
}

function normalizePage<T>(
  data: PaginatedAgendaResponse<T> | T[],
): PaginatedAgendaResponse<T> {
  if (Array.isArray(data)) {
    return {
      pagination: {
        count: data.length,
        total_pages: 1,
        current_page: 1,
        next: null,
        previous: null,
      },
      results: data,
    };
  }
  return data;
}

async function listAppointmentPage(filters?: AppointmentFilters) {
  const query = buildParams(filters as Record<string, unknown>);
  const response = await api.get<
    PaginatedAgendaResponse<AgendaAppointment> | AgendaAppointment[]
  >(`agenda/appointments/${query ? `?${query}` : ""}`);
  return normalizePage(response.data);
}

async function listLegacyAppointments(
  filters?: AppointmentFilters,
): Promise<LegacyAppointment[]> {
  const page = await listAppointmentPage(filters);
  return page.results as unknown as LegacyAppointment[];
}

export const agendaService = {
  list: listLegacyAppointments,

  appointments: {
    list: listAppointmentPage,
    get: async (id: number) =>
      (await api.get<AgendaAppointment>(`agenda/appointments/${id}/`)).data,
    create: async (payload: CreateAppointmentPayload) =>
      (await api.post<AgendaAppointment>("agenda/appointments/", payload)).data,
    update: async (id: number, payload: Partial<CreateAppointmentPayload>) =>
      (
        await api.patch<AgendaAppointment>(
          `agenda/appointments/${id}/`,
          payload,
        )
      ).data,
    transition: async (
      id: number,
      action: "confirm" | "cancel" | "complete" | "mark-no-show",
      payload?: Record<string, unknown>,
    ) =>
      (
        await api.post<AgendaAppointment>(
          `agenda/appointments/${id}/${action}/`,
          payload || {},
        )
      ).data,
    reschedule: async (
      id: number,
      payload: Partial<CreateAppointmentPayload>,
    ) =>
      (
        await api.post<AgendaAppointment>(
          `agenda/appointments/${id}/reschedule/`,
          payload,
        )
      ).data,
    remove: async (id: number) => {
      await api.delete(`agenda/appointments/${id}/`);
    },
    checkAvailability: async (payload: {
      date: string;
      duration: number;
      therapist_id?: number;
      patient_id?: number;
      room_id?: number;
    }) =>
      (
        await api.post<TimeSlot[]>(
          "agenda/appointments/check-availability/",
          payload,
        )
      ).data,
    exportUrl: (filters?: AppointmentFilters) => {
      const query = buildParams(filters as Record<string, unknown>);
      return `agenda/appointments/export/${query ? `?${query}` : ""}`;
    },
  },

  rooms: {
    list: async () => {
      const response = await api.get<
        AgendaRoom[] | PaginatedAgendaResponse<AgendaRoom>
      >("agenda/rooms/?page_size=100");
      return Array.isArray(response.data)
        ? response.data
        : response.data.results;
    },
  },

  blocks: {
    list: async (filters?: Record<string, unknown>) => {
      const query = buildParams(filters);
      const response = await api.get<PaginatedAgendaResponse<ScheduleBlock>>(
        `agenda/schedule-blocks/${query ? `?${query}` : ""}`,
      );
      return normalizePage(response.data);
    },
    create: async (payload: CreateScheduleBlockPayload) =>
      (await api.post<ScheduleBlock>("agenda/schedule-blocks/", payload)).data,
    update: async (id: number, payload: Partial<CreateScheduleBlockPayload>) =>
      (await api.patch<ScheduleBlock>(`agenda/schedule-blocks/${id}/`, payload))
        .data,
    remove: async (id: number) => {
      await api.delete(`agenda/schedule-blocks/${id}/`);
    },
  },

  recurrences: {
    list: async (filters?: Record<string, unknown>) => {
      const query = buildParams(filters);
      const response = await api.get<
        PaginatedAgendaResponse<AppointmentRecurrence>
      >(`agenda/appointment-recurrences/${query ? `?${query}` : ""}`);
      return normalizePage(response.data);
    },
    update: async (id: number, payload: Record<string, unknown>) =>
      (
        await api.patch<AppointmentRecurrence>(
          `agenda/appointment-recurrences/${id}/`,
          payload,
        )
      ).data,
    action: async (id: number, action: "pause" | "reactivate" | "end") =>
      (
        await api.post<AppointmentRecurrence>(
          `agenda/appointment-recurrences/${id}/${action}/`,
          {},
        )
      ).data,
    applyChange: async (
      id: number,
      payload: {
        scope: "occurrence" | "following" | "all";
        occurrence_id: number;
        changes: Record<string, unknown>;
      },
    ) =>
      (
        await api.post(
          `agenda/appointment-recurrences/${id}/apply-change/`,
          payload,
        )
      ).data,
  },

  packages: {
    list: async (filters?: Record<string, unknown>) => {
      const query = buildParams(filters);
      const response = await api.get<PaginatedAgendaResponse<PatientPackage>>(
        `agenda/patient-packages/${query ? `?${query}` : ""}`,
      );
      return normalizePage(response.data);
    },
    create: async (payload: CreatePackagePayload) =>
      (await api.post<PatientPackage>("agenda/patient-packages/", payload))
        .data,
    update: async (id: number, payload: Partial<CreatePackagePayload>) =>
      (
        await api.patch<PatientPackage>(
          `agenda/patient-packages/${id}/`,
          payload,
        )
      ).data,
    addSession: async (id: number, payload: CreateAppointmentPayload) =>
      (
        await api.post<AgendaAppointment>(
          `agenda/patient-packages/${id}/add-session/`,
          payload,
        )
      ).data,
    action: async (id: number, action: "cancel" | "renew", payload = {}) =>
      (
        await api.post<PatientPackage>(
          `agenda/patient-packages/${id}/${action}/`,
          payload,
        )
      ).data,
    removeSession: async (sessionId: number) => {
      await api.delete(`agenda/package-sessions/${sessionId}/`);
    },
  },

  telemedicine: {
    list: async (filters?: Record<string, unknown>) => {
      const query = buildParams(filters);
      const response = await api.get<PaginatedAgendaResponse<TelemedicineRoom>>(
        `agenda/telemedicine/${query ? `?${query}` : ""}`,
      );
      return normalizePage(response.data);
    },
    regenerate: async (id: number) =>
      (
        await api.post<TelemedicineRoom>(
          `agenda/telemedicine/${id}/regenerate-link/`,
          {},
        )
      ).data,
    open: async (id: number) =>
      (
        await api.post<{ professional_link: string }>(
          `agenda/telemedicine/${id}/open-room/`,
          {},
        )
      ).data,
  },
};
