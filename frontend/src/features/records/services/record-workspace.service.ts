import { api } from "@/lib/api";
import type {
  AnamnesisWorkspace,
  ClinicalDocument,
  EvolutionPayload,
  EvolutionWorkspace,
  Paginated,
  RecordSummary,
  TreatmentGoal,
} from "../types";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export const recordWorkspaceService = {
  getSummary: async (patientId: number) => {
    const response = await api.get<RecordSummary>(
      `records/patients/${patientId}/workspace/`,
    );
    return response.data;
  },

  listEvolutions: async (patientId: number, page = 1, status?: string) => {
    const params = new URLSearchParams({ page: String(page), page_size: "10" });
    if (status) params.set("status", status);
    const response = await api.get<Paginated<EvolutionWorkspace>>(
      `records/patients/${patientId}/clinical-evolutions/?${params.toString()}`,
    );
    return response.data;
  },

  getEvolution: async (id: number) => {
    const response = await api.get<EvolutionWorkspace>(
      `records/clinical-evolutions/${id}/`,
    );
    return response.data;
  },

  createEvolution: async (patientId: number, payload: EvolutionPayload) => {
    const response = await api.post<EvolutionWorkspace>(
      `records/patients/${patientId}/clinical-evolutions/`,
      payload,
    );
    return response.data;
  },

  updateEvolution: async (id: number, payload: Partial<EvolutionPayload>) => {
    const response = await api.patch<EvolutionWorkspace>(
      `records/clinical-evolutions/${id}/`,
      payload,
    );
    return response.data;
  },

  finalizeEvolution: async (id: number) => {
    const response = await api.post<EvolutionWorkspace>(
      `records/clinical-evolutions/${id}/finalize/`,
    );
    return response.data;
  },

  duplicateEvolution: async (id: number, sessionDate: string) => {
    const response = await api.post<EvolutionWorkspace>(
      `records/clinical-evolutions/${id}/duplicate/`,
      { session_date: sessionDate },
    );
    return response.data;
  },

  getAnamnesis: async (patientId: number) => {
    const response = await api.get<AnamnesisWorkspace>(
      `records/patients/${patientId}/clinical-anamnesis/`,
    );
    return response.data;
  },

  saveAnamnesis: async (
    patientId: number,
    payload: Partial<AnamnesisWorkspace>,
  ) => {
    const response = await api.patch<AnamnesisWorkspace>(
      `records/patients/${patientId}/clinical-anamnesis/`,
      payload,
    );
    return response.data;
  },

  listGoals: async (patientId: number) => {
    const response = await api.get<TreatmentGoal[]>(
      `records/patients/${patientId}/goals/`,
    );
    return response.data;
  },

  createGoal: async (patientId: number, payload: Partial<TreatmentGoal>) => {
    const response = await api.post<TreatmentGoal>(
      `records/patients/${patientId}/goals/`,
      payload,
    );
    return response.data;
  },

  updateGoal: async (id: number, payload: Partial<TreatmentGoal>) => {
    const response = await api.patch<TreatmentGoal>(
      `records/goals/${id}/`,
      payload,
    );
    return response.data;
  },

  archiveGoal: async (id: number) => {
    await api.delete(`records/goals/${id}/`);
  },

  listDocuments: async (patientId: number) => {
    const response = await api.get<ClinicalDocument[]>(
      `records/patients/${patientId}/documents/`,
    );
    return response.data;
  },

  uploadDocument: async (patientId: number, formData: FormData) => {
    const response = await api.post<ClinicalDocument>(
      `records/patients/${patientId}/documents/`,
      formData,
    );
    return response.data;
  },

  updateDocument: async (id: number, payload: Partial<ClinicalDocument>) => {
    const response = await api.patch<ClinicalDocument>(
      `records/documents/${id}/`,
      payload,
    );
    return response.data;
  },

  archiveDocument: async (id: number) => {
    await api.delete(`records/documents/${id}/`);
  },

  downloadDocument: async (document: ClinicalDocument) => {
    if (document.scan_status !== "clean" || !document.download_url) {
      window.alert(
        document.status_display ??
          "O arquivo ainda não está disponível para download.",
      );
      return;
    }
    const response = await api.get(
      `records/documents/${document.id}/download/`,
      {
        responseType: "blob",
      },
    );
    downloadBlob(response.data, document.original_name);
  },

  exportPatientPdf: async (patientId: number) => {
    const response = await api.get(
      `records/patients/${patientId}/export-pdf/`,
      {
        responseType: "blob",
      },
    );
    downloadBlob(response.data, `prontuario-paciente-${patientId}.pdf`);
  },

  listForms: async (patientId: number, search?: string) => {
    const url = search
      ? `records/patients/${patientId}/forms/?search=${encodeURIComponent(search)}`
      : `records/patients/${patientId}/forms/`;
    const response = await api.get<any[]>(url);
    return response.data;
  },

  submitForm: async (patientId: number, payload: any) => {
    const response = await api.post<any>(
      `records/patients/${patientId}/forms/`,
      payload,
    );
    return response.data;
  },

  listExports: async (patientId: number) => {
    const response = await api.get<any[]>(
      `records/patients/${patientId}/exports/`,
    );
    return response.data;
  },

  createExport: async (
    patientId: number,
    exportType: string,
    period: string,
  ) => {
    const response = await api.post<any>(
      `records/patients/${patientId}/exports/`,
      {
        export_type: exportType,
        period: period,
      },
    );
    return response.data;
  },

  retryExport: async (exportId: number) => {
    const response = await api.post<any>(`records/exports/${exportId}/retry/`);
    return response.data;
  },

  downloadExport: async (exportId: number, filename: string) => {
    const response = await api.get(`records/exports/${exportId}/download/`, {
      responseType: "blob",
    });
    downloadBlob(response.data, filename);
  },
};
