import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { formsService } from "./forms.service";
import type { FormFilters, FormPayload } from "./types";

export function useForms(filters?: FormFilters) {
  return useQuery({ queryKey: ["forms", filters], queryFn: () => formsService.list(filters) });
}

export function useFormTemplates(filters?: FormFilters) {
  return useQuery({ queryKey: ["form-templates", filters], queryFn: () => formsService.templates(filters) });
}

export function useCreateForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: FormPayload) => formsService.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["forms"] }),
  });
}

export function useUpdateForm() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<FormPayload> }) => formsService.update(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["forms"] }),
  });
}

export function useCreateFormFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, payload }: { templateId: number; payload: FormPayload }) => formsService.createFromTemplate(templateId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["forms"] }),
  });
}

export function useFormAction(action: "duplicate" | "archive" | "restore" | "remove") {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number): Promise<unknown> => {
      if (action === "duplicate") return formsService.duplicate(id);
      if (action === "archive") return formsService.archive(id);
      if (action === "restore") return formsService.restore(id);
      await formsService.remove(id);
      return null;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["forms"] }),
  });
}
