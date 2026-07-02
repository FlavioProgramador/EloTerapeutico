import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { agendaService } from "../services/agenda.service";
import type {
  AppointmentFilters,
  CreateAppointmentPayload,
  CreatePackagePayload,
  CreateScheduleBlockPayload,
} from "../types";

export const AGENDA_QUERY_KEYS = {
  appointments: ["agenda", "appointments"] as const,
  appointment: (id: number) => ["agenda", "appointments", id] as const,
  rooms: ["agenda", "rooms"] as const,
  blocks: ["agenda", "blocks"] as const,
  recurrences: ["agenda", "recurrences"] as const,
  packages: ["agenda", "packages"] as const,
  telemedicine: ["agenda", "telemedicine"] as const,
  availability: ["agenda", "availability"] as const,
};

function getErrorMessage(error: unknown, fallback: string) {
  if (!error || typeof error !== "object" || !("response" in error)) return fallback;
  const data = (error as { response?: { data?: unknown } }).response?.data;
  if (!data || typeof data !== "object") return fallback;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  for (const value of Object.values(record)) {
    if (typeof value === "string") return value;
    if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  }
  return fallback;
}

function useInvalidateAgenda() {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.appointments }),
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.blocks }),
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.recurrences }),
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.packages }),
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.telemedicine }),
      queryClient.invalidateQueries({ queryKey: AGENDA_QUERY_KEYS.availability }),
    ]);
}

export function useAppointments(filters?: AppointmentFilters) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.appointments, filters],
    queryFn: () => agendaService.appointments.list(filters),
  });
}

export function useAppointment(id?: number) {
  return useQuery({
    queryKey: AGENDA_QUERY_KEYS.appointment(id || 0),
    queryFn: () => agendaService.appointments.get(id!),
    enabled: Boolean(id),
  });
}

export function useRooms() {
  return useQuery({
    queryKey: AGENDA_QUERY_KEYS.rooms,
    queryFn: agendaService.rooms.list,
    staleTime: 60_000,
  });
}

export function useScheduleBlocks(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.blocks, filters],
    queryFn: () => agendaService.blocks.list(filters),
  });
}

export function useRecurrences(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.recurrences, filters],
    queryFn: () => agendaService.recurrences.list(filters),
  });
}

export function usePackages(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.packages, filters],
    queryFn: () => agendaService.packages.list(filters),
  });
}

export function useTelemedicine(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.telemedicine, filters],
    queryFn: () => agendaService.telemedicine.list(filters),
  });
}

export function useAvailableSlots(
  payload: {
    date: string;
    duration: number;
    therapist_id?: number;
    patient_id?: number;
    room_id?: number;
  },
  enabled = true,
) {
  return useQuery({
    queryKey: [...AGENDA_QUERY_KEYS.availability, payload],
    queryFn: () => agendaService.appointments.checkAvailability(payload),
    enabled: enabled && Boolean(payload.date && payload.duration),
    staleTime: 5_000,
  });
}

export function useCreateAppointment() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (payload: CreateAppointmentPayload) =>
      agendaService.appointments.create(payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Consulta agendada com sucesso.");
    },
    onError: (error) =>
      toast.error("Não foi possível agendar.", {
        description: getErrorMessage(
          error,
          "Revise os campos e os conflitos de horário.",
        ),
      }),
  });
}

export function useUpdateAppointment(id: number) {
  const invalidate = useInvalidateAgenda();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<CreateAppointmentPayload>) =>
      agendaService.appointments.update(id, payload),
    onSuccess: async () => {
      await invalidate();
      await queryClient.invalidateQueries({
        queryKey: AGENDA_QUERY_KEYS.appointment(id),
      });
      toast.success("Consulta atualizada.");
    },
    onError: (error) =>
      toast.error("Não foi possível atualizar.", {
        description: getErrorMessage(error, "Verifique os conflitos de horário."),
      }),
  });
}

export function useAppointmentTransition() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: ({
      id,
      action,
      payload,
    }: {
      id: number;
      action: "confirm" | "cancel" | "complete" | "mark-no-show";
      payload?: Record<string, unknown>;
    }) => agendaService.appointments.transition(id, action, payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Status da consulta atualizado.");
    },
    onError: (error) =>
      toast.error("Não foi possível alterar o status.", {
        description: getErrorMessage(error, "Tente novamente."),
      }),
  });
}

export function useCreateScheduleBlock() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (payload: CreateScheduleBlockPayload) =>
      agendaService.blocks.create(payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Horário bloqueado.");
    },
    onError: (error) =>
      toast.error("Não foi possível bloquear o horário.", {
        description: getErrorMessage(
          error,
          "Verifique consultas e bloqueios existentes.",
        ),
      }),
  });
}

export function useCreatePackage() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (payload: CreatePackagePayload) =>
      agendaService.packages.create(payload),
    onSuccess: async () => {
      await invalidate();
      toast.success("Pacote criado com sucesso.");
    },
    onError: (error) =>
      toast.error("Não foi possível criar o pacote.", {
        description: getErrorMessage(error, "Revise os dados informados."),
      }),
  });
}

export function useRecurrenceAction() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "pause" | "reactivate" | "end";
    }) => agendaService.recurrences.action(id, action),
    onSuccess: async () => {
      await invalidate();
      toast.success("Recorrência atualizada.");
    },
  });
}

export function useTelemedicineAction() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "regenerate" | "open" }) =>
      action === "regenerate"
        ? agendaService.telemedicine.regenerate(id)
        : agendaService.telemedicine.open(id),
    onSuccess: async (data, variables) => {
      await invalidate();
      if (variables.action === "open" && "professional_link" in data) {
        window.open(data.professional_link, "_blank", "noopener,noreferrer");
      } else {
        toast.success("Link de telemedicina atualizado.");
      }
    },
  });
}
