import { api } from "@/lib/api";
import type {
  DocumentFilters,
  DocumentTemplate,
  DocumentTemplatePayload,
  EvolutionTemplate,
  EvolutionTemplatePayload,
  GeneratedDocument,
  PaginatedGeneratedDocuments,
  PaginatedTemplates,
  PlaceholderDefinition,
} from "../types";

function paramsFrom(filters?: DocumentFilters) {
  const params = new URLSearchParams();
  if (!filters) return params;
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  return params;
}

export const documentsService = {
  listTemplates: async (filters?: DocumentFilters): Promise<PaginatedTemplates> => {
    const response = await api.get<PaginatedTemplates>("documents/templates/", {
      params: paramsFrom(filters),
    });
    return response.data;
  },
  getTemplate: async (publicId: string): Promise<DocumentTemplate> => {
    const response = await api.get<DocumentTemplate>(`documents/templates/${publicId}/`);
    return response.data;
  },
  createTemplate: async (payload: DocumentTemplatePayload): Promise<DocumentTemplate> => {
    const response = await api.post<DocumentTemplate>("documents/templates/", payload);
    return response.data;
  },
  updateTemplate: async (
    publicId: string,
    payload: Partial<DocumentTemplatePayload>,
  ): Promise<DocumentTemplate> => {
    const response = await api.patch<DocumentTemplate>(
      `documents/templates/${publicId}/`,
      payload,
    );
    return response.data;
  },
  templateAction: async (
    publicId: string,
    action: "duplicate" | "archive" | "activate" | "deactivate",
  ): Promise<DocumentTemplate> => {
    const response = await api.post<DocumentTemplate>(
      `documents/templates/${publicId}/${action}/`,
    );
    return response.data;
  },
  previewTemplate: async (
    publicId: string,
    payload?: { patient_id?: number; local_emissao?: string },
    library = false,
  ): Promise<{ title: string; header_html: string; content_html: string; footer_html: string }> => {
    const scope = library ? "library" : "templates";
    const response = await api.post(
      `documents/${scope}/${publicId}/preview/`,
      payload ?? {},
    );
    return response.data;
  },
  listLibrary: async (filters?: DocumentFilters): Promise<PaginatedTemplates> => {
    const response = await api.get<PaginatedTemplates>("documents/library/", {
      params: paramsFrom(filters),
    });
    return response.data;
  },
  importLibraryTemplate: async (publicId: string): Promise<DocumentTemplate> => {
    const response = await api.post<DocumentTemplate>(
      `documents/library/${publicId}/import/`,
    );
    return response.data;
  },
  placeholders: async (): Promise<PlaceholderDefinition[]> => {
    const response = await api.get<PlaceholderDefinition[]>("documents/placeholders/");
    return response.data;
  },
  listGenerated: async (
    filters?: DocumentFilters,
  ): Promise<PaginatedGeneratedDocuments> => {
    const response = await api.get<PaginatedGeneratedDocuments>("documents/generated/", {
      params: paramsFrom(filters),
    });
    return response.data;
  },
  getGenerated: async (publicId: string): Promise<GeneratedDocument> => {
    const response = await api.get<GeneratedDocument>(`documents/generated/${publicId}/`);
    return response.data;
  },
  createGenerated: async (payload: {
    template_public_id: string;
    patient_id: number;
    title?: string;
    local_emissao?: string;
  }): Promise<GeneratedDocument> => {
    const response = await api.post<GeneratedDocument>("documents/generated/", payload, {
      headers: { "Idempotency-Key": crypto.randomUUID() },
    });
    return response.data;
  },
  updateGenerated: async (
    publicId: string,
    payload: { title?: string; draft_content?: string },
  ): Promise<GeneratedDocument> => {
    const response = await api.patch<GeneratedDocument>(
      `documents/generated/${publicId}/`,
      payload,
    );
    return response.data;
  },
  generatedAction: async (
    publicId: string,
    action: "generate" | "archive" | "cancel",
  ): Promise<GeneratedDocument> => {
    const response = await api.post<GeneratedDocument>(
      `documents/generated/${publicId}/${action}/`,
    );
    return response.data;
  },
  downloadGenerated: async (publicId: string, filename: string): Promise<void> => {
    const response = await api.get<Blob>(
      `documents/generated/${publicId}/download/`,
      { responseType: "blob" },
    );
    const url = URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
  listEvolutionTemplates: async (filters?: {
    search?: string;
    status?: string;
    category?: string;
    specialty?: string;
  }): Promise<EvolutionTemplate[]> => {
    const params = new URLSearchParams({ include_inactive: "true" });
    Object.entries(filters ?? {}).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const response = await api.get<EvolutionTemplate[]>(
      `records/clinical-templates/?${params.toString()}`,
    );
    return response.data;
  },
  createEvolutionTemplate: async (
    payload: EvolutionTemplatePayload,
  ): Promise<EvolutionTemplate> => {
    const response = await api.post<EvolutionTemplate>(
      "records/clinical-templates/",
      payload,
    );
    return response.data;
  },
  updateEvolutionTemplate: async (
    id: number,
    payload: Partial<EvolutionTemplatePayload>,
  ): Promise<EvolutionTemplate> => {
    const response = await api.patch<EvolutionTemplate>(
      `records/clinical-templates/${id}/`,
      payload,
    );
    return response.data;
  },
  evolutionTemplateAction: async (
    id: number,
    action: "duplicate" | "activate" | "deactivate" | "archive" | "mark_used",
  ): Promise<EvolutionTemplate> => {
    const response = await api.post<EvolutionTemplate>(
      `records/clinical-templates/${id}/`,
      { action },
    );
    return response.data;
  },
};
