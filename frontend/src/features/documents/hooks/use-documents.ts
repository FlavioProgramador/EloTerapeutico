"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { extractApiError } from "@/lib/utils";
import { documentsService } from "../services/documents.service";
import type {
  DocumentFilters,
  DocumentTemplatePayload,
  EvolutionTemplatePayload,
} from "../types";

const keys = {
  templates: (filters?: DocumentFilters) =>
    ["documents", "templates", filters] as const,
  library: (filters?: DocumentFilters) =>
    ["documents", "library", filters] as const,
  generated: (filters?: DocumentFilters) =>
    ["documents", "generated", filters] as const,
  placeholders: ["documents", "placeholders"] as const,
  evolution: (filters?: Record<string, string | undefined>) =>
    ["documents", "evolution-templates", filters] as const,
};

export function useDocumentTemplates(filters?: DocumentFilters) {
  return useQuery({
    queryKey: keys.templates(filters),
    queryFn: () => documentsService.listTemplates(filters),
  });
}

export function useDocumentLibrary(filters?: DocumentFilters) {
  return useQuery({
    queryKey: keys.library(filters),
    queryFn: () => documentsService.listLibrary(filters),
  });
}

export function useGeneratedDocuments(filters?: DocumentFilters) {
  return useQuery({
    queryKey: keys.generated(filters),
    queryFn: () => documentsService.listGenerated(filters),
  });
}

export function usePlaceholders() {
  return useQuery({
    queryKey: keys.placeholders,
    queryFn: documentsService.placeholders,
  });
}

export function useEvolutionTemplates(
  filters?: Record<string, string | undefined>,
) {
  return useQuery({
    queryKey: keys.evolution(filters),
    queryFn: () => documentsService.listEvolutionTemplates(filters),
  });
}

function useDocumentMutation<TVariables, TResult>(
  mutationFn: (variables: TVariables) => Promise<TResult>,
  successMessage: string,
  invalidate: (queryClient: ReturnType<typeof useQueryClient>) => void,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      invalidate(queryClient);
      toast.success(successMessage);
    },
    onError: (error) => toast.error(extractApiError(error)),
  });
}

export function useCreateDocumentTemplate() {
  return useDocumentMutation<DocumentTemplatePayload, unknown>(
    documentsService.createTemplate,
    "Template criado com sucesso.",
    (client) =>
      client.invalidateQueries({ queryKey: ["documents", "templates"] }),
  );
}

export function useUpdateDocumentTemplate() {
  return useDocumentMutation<
    { publicId: string; payload: Partial<DocumentTemplatePayload> },
    unknown
  >(
    ({ publicId, payload }) =>
      documentsService.updateTemplate(publicId, payload),
    "Template atualizado com sucesso.",
    (client) =>
      client.invalidateQueries({ queryKey: ["documents", "templates"] }),
  );
}

export function useTemplateAction() {
  return useDocumentMutation<
    {
      publicId: string;
      action: "duplicate" | "archive" | "activate" | "deactivate";
    },
    unknown
  >(
    ({ publicId, action }) => documentsService.templateAction(publicId, action),
    "Template atualizado.",
    (client) =>
      client.invalidateQueries({ queryKey: ["documents", "templates"] }),
  );
}

export function useImportLibraryTemplate() {
  return useDocumentMutation<string, unknown>(
    documentsService.importLibraryTemplate,
    "Template importado para sua biblioteca.",
    (client) => {
      client.invalidateQueries({ queryKey: ["documents", "templates"] });
      client.invalidateQueries({ queryKey: ["documents", "library"] });
    },
  );
}

export function useCreateGeneratedDocument() {
  return useDocumentMutation<
    {
      template_public_id: string;
      patient_id: number;
      title?: string;
      local_emissao?: string;
    },
    { public_id: string }
  >(
    documentsService.createGenerated,
    "Rascunho criado. Revise e gere o PDF.",
    (client) =>
      client.invalidateQueries({ queryKey: ["documents", "generated"] }),
  );
}

export function useGeneratedDocumentAction() {
  return useDocumentMutation<
    { publicId: string; action: "generate" | "archive" | "cancel" },
    unknown
  >(
    ({ publicId, action }) =>
      documentsService.generatedAction(publicId, action),
    "Documento atualizado.",
    (client) =>
      client.invalidateQueries({ queryKey: ["documents", "generated"] }),
  );
}

export function useCreateEvolutionTemplate() {
  return useDocumentMutation<EvolutionTemplatePayload, unknown>(
    documentsService.createEvolutionTemplate,
    "Template de evolução criado.",
    (client) =>
      client.invalidateQueries({
        queryKey: ["documents", "evolution-templates"],
      }),
  );
}

export function useUpdateEvolutionTemplate() {
  return useDocumentMutation<
    { id: number; payload: Partial<EvolutionTemplatePayload> },
    unknown
  >(
    ({ id, payload }) => documentsService.updateEvolutionTemplate(id, payload),
    "Template de evolução atualizado.",
    (client) =>
      client.invalidateQueries({
        queryKey: ["documents", "evolution-templates"],
      }),
  );
}

export function useEvolutionTemplateAction() {
  return useDocumentMutation<
    { id: number; action: "duplicate" | "activate" | "deactivate" | "archive" },
    unknown
  >(
    ({ id, action }) => documentsService.evolutionTemplateAction(id, action),
    "Template de evolução atualizado.",
    (client) =>
      client.invalidateQueries({
        queryKey: ["documents", "evolution-templates"],
      }),
  );
}
