import type { Appointment } from "@/types";
import type { AppointmentFilters } from "../types";
import { agendaService as baseAgendaService } from "./agenda.service";

export const agendaService = {
  ...baseAgendaService,
  list: async (filters?: AppointmentFilters): Promise<Appointment[]> => {
    const page = await baseAgendaService.appointments.list(filters);
    return page.results as unknown as Appointment[];
  },
};
