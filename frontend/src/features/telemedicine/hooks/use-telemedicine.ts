import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { telemedicineProfessionalService } from "../services/telemedicine.service";
import type { TelemedicineDashboardRoom } from "../types";

interface TelemedicinePage {
  pagination: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  results: TelemedicineDashboardRoom[];
}

export const TELEMEDICINE_QUERY_KEY = [
  "agenda",
  "telemedicine",
  "secure",
] as const;

function buildQuery(filters?: Record<string, unknown>) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters || {})) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  return params.toString();
}

export function useTelemedicineRooms(filters?: Record<string, unknown>) {
  return useQuery({
    queryKey: [...TELEMEDICINE_QUERY_KEY, filters],
    queryFn: async () => {
      const query = buildQuery(filters);
      const response = await api.get<TelemedicinePage>(
        `scheduling/telemedicine/${query ? `?${query}` : ""}`,
      );
      return response.data;
    },
  });
}

export function useCreateTelemedicineInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: telemedicineProfessionalService.createInvitation,
    onSuccess: async (data) => {
      await navigator.clipboard.writeText(data.invitation_url);
      await queryClient.invalidateQueries({ queryKey: TELEMEDICINE_QUERY_KEY });
      toast.success("Convite criado e copiado.");
    },
    onError: () => toast.error("Não foi possível criar o convite."),
  });
}

export function useSendTelemedicineInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      roomId,
      channel = "email",
    }: {
      roomId: number;
      channel?: "email" | "whatsapp_manual";
    }) => telemedicineProfessionalService.sendInvitation(roomId, channel),
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: TELEMEDICINE_QUERY_KEY });
      toast.success(
        data.channel === "email"
          ? "Convite enfileirado para envio por e-mail."
          : "Convite preparado para envio manual pelo WhatsApp.",
      );
    },
    onError: () => toast.error("Não foi possível enviar o convite."),
  });
}

export function useRevokeTelemedicineInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: telemedicineProfessionalService.revokeInvitation,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: TELEMEDICINE_QUERY_KEY });
      toast.success("Convite revogado.");
    },
    onError: () => toast.error("Não foi possível revogar o convite."),
  });
}
