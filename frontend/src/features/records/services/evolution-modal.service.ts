import { api } from "@/lib/api";
import type { EvolutionWorkspace } from "../types";
import type {
  ClinicalEvolutionTemplate,
  EvolutionAppointmentOption,
  EvolutionAttachment,
  EvolutionModalPayload,
} from "../evolution-modal.types";

export const evolutionModalService = {
  listAppointments: async (patientId: number) => {
    const response = await api.get<EvolutionAppointmentOption[]>(
      `records/patients/${patientId}/evolution-appointments/`,
    );
    return response.data;
  },

  listTemplates: async () => {
    const response = await api.get<ClinicalEvolutionTemplate[]>(
      "records/clinical-templates/",
    );
    return response.data;
  },

  create: async (patientId: number, payload: EvolutionModalPayload) => {
    const response = await api.post<EvolutionWorkspace>(
      `records/patients/${patientId}/clinical-evolutions/`,
      payload,
    );
    return response.data;
  },

  update: async (evolutionId: number, payload: Partial<EvolutionModalPayload>) => {
    const response = await api.patch<EvolutionWorkspace>(
      `records/clinical-evolutions/${evolutionId}/`,
      payload,
    );
    return response.data;
  },

  uploadAttachment: async (
    evolutionId: number,
    file: File,
    onProgress: (progress: number) => void,
  ) => {
    const body = new FormData();
    body.append("file", file, file.name);
    const response = await api.post<EvolutionAttachment>(
      `records/clinical-evolutions/${evolutionId}/attachments/`,
      body,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (!event.total) return;
          onProgress(Math.round((event.loaded / event.total) * 100));
        },
      },
    );
    return response.data;
  },

  removeAttachment: async (evolutionId: number, attachmentId: number) => {
    await api.delete(
      `records/clinical-evolutions/${evolutionId}/attachments/${attachmentId}/`,
    );
  },
};
