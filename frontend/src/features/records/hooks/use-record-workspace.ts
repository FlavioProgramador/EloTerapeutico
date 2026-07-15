import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { recordWorkspaceService } from "../services/record-workspace.service";
import type {
  AnamnesisWorkspace,
  ClinicalDocument,
  EvolutionPayload,
  TreatmentGoal,
} from "../types";

const keys = {
  summary: (patientId: number) =>
    ["record-workspace", patientId, "summary"] as const,
  evolutions: (patientId: number, page = 1, status?: string) =>
    [
      "record-workspace",
      patientId,
      "evolutions",
      page,
      status ?? "all",
    ] as const,
  evolution: (id: number) => ["record-workspace", "evolution", id] as const,
  anamnesis: (patientId: number) =>
    ["record-workspace", patientId, "anamnesis"] as const,
  goals: (patientId: number) =>
    ["record-workspace", patientId, "goals"] as const,
  documents: (patientId: number) =>
    ["record-workspace", patientId, "documents"] as const,
};

export function useRecordSummary(patientId: number) {
  return useQuery({
    queryKey: keys.summary(patientId),
    queryFn: () => recordWorkspaceService.getSummary(patientId),
    enabled: Number.isFinite(patientId) && patientId > 0,
  });
}

export function useClinicalEvolutions(
  patientId: number,
  page = 1,
  status?: string,
  enabled = true,
) {
  return useQuery({
    queryKey: keys.evolutions(patientId, page, status),
    queryFn: () =>
      recordWorkspaceService.listEvolutions(patientId, page, status),
    enabled: enabled && Number.isFinite(patientId) && patientId > 0,
  });
}

export function useClinicalEvolution(id?: number | null) {
  return useQuery({
    queryKey: keys.evolution(id ?? 0),
    queryFn: () => recordWorkspaceService.getEvolution(id!),
    enabled: Boolean(id),
  });
}

export function useCreateClinicalEvolution(patientId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: EvolutionPayload) =>
      recordWorkspaceService.createEvolution(patientId, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["record-workspace", patientId] });
      toast.success("Evolução salva como rascunho.");
    },
    onError: () => toast.error("Não foi possível salvar a evolução."),
  });
}

export function useUpdateClinicalEvolution(
  patientId: number,
  evolutionId?: number | null,
) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<EvolutionPayload>) =>
      recordWorkspaceService.updateEvolution(evolutionId!, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["record-workspace", patientId] });
      if (evolutionId)
        client.invalidateQueries({ queryKey: keys.evolution(evolutionId) });
      toast.success("Alterações salvas.");
    },
    onError: () => toast.error("Não foi possível atualizar a evolução."),
  });
}

export function useFinalizeClinicalEvolution(patientId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => recordWorkspaceService.finalizeEvolution(id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["record-workspace", patientId] });
      toast.success("Evolução finalizada e bloqueada para edição direta.");
    },
    onError: () => toast.error("Não foi possível finalizar a evolução."),
  });
}

export function useDuplicateClinicalEvolution(patientId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, sessionDate }: { id: number; sessionDate: string }) =>
      recordWorkspaceService.duplicateEvolution(id, sessionDate),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: ["record-workspace", patientId] });
      toast.success("Novo rascunho criado a partir da evolução.");
    },
    onError: () => toast.error("Não foi possível duplicar a evolução."),
  });
}

export function useClinicalAnamnesis(patientId: number, enabled = true) {
  return useQuery({
    queryKey: keys.anamnesis(patientId),
    queryFn: () => recordWorkspaceService.getAnamnesis(patientId),
    enabled: enabled && patientId > 0,
  });
}

export function useSaveClinicalAnamnesis(patientId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<AnamnesisWorkspace>) =>
      recordWorkspaceService.saveAnamnesis(patientId, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: keys.anamnesis(patientId) });
      client.invalidateQueries({ queryKey: keys.summary(patientId) });
      toast.success("Seção da anamnese salva.");
    },
    onError: () => toast.error("Não foi possível salvar a anamnese."),
  });
}

export function useTreatmentGoals(patientId: number, enabled = true) {
  return useQuery({
    queryKey: keys.goals(patientId),
    queryFn: () => recordWorkspaceService.listGoals(patientId),
    enabled: enabled && patientId > 0,
  });
}

export function useGoalMutations(patientId: number) {
  const client = useQueryClient();
  const invalidate = () => {
    client.invalidateQueries({ queryKey: keys.goals(patientId) });
    client.invalidateQueries({ queryKey: keys.summary(patientId) });
  };
  const create = useMutation({
    mutationFn: (payload: Partial<TreatmentGoal>) =>
      recordWorkspaceService.createGoal(patientId, payload),
    onSuccess: () => {
      invalidate();
      toast.success("Meta terapêutica criada.");
    },
    onError: () => toast.error("Não foi possível criar a meta."),
  });
  const update = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: Partial<TreatmentGoal>;
    }) => recordWorkspaceService.updateGoal(id, payload),
    onSuccess: () => {
      invalidate();
      toast.success("Meta terapêutica atualizada.");
    },
    onError: () => toast.error("Não foi possível atualizar a meta."),
  });
  const archive = useMutation({
    mutationFn: (id: number) => recordWorkspaceService.archiveGoal(id),
    onSuccess: () => {
      invalidate();
      toast.success("Meta arquivada.");
    },
    onError: () => toast.error("Não foi possível arquivar a meta."),
  });
  return { create, update, archive };
}

export function useClinicalDocuments(patientId: number, enabled = true) {
  return useQuery({
    queryKey: keys.documents(patientId),
    queryFn: () => recordWorkspaceService.listDocuments(patientId),
    enabled: enabled && patientId > 0,
  });
}

export function useDocumentMutations(patientId: number) {
  const client = useQueryClient();
  const invalidate = () => {
    client.invalidateQueries({ queryKey: keys.documents(patientId) });
    client.invalidateQueries({ queryKey: keys.summary(patientId) });
  };
  const upload = useMutation({
    mutationFn: (formData: FormData) =>
      recordWorkspaceService.uploadDocument(patientId, formData),
    onSuccess: () => {
      invalidate();
      toast.success("Documento anexado com segurança.");
    },
    onError: () => toast.error("Não foi possível anexar o documento."),
  });
  const update = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: Partial<ClinicalDocument>;
    }) => recordWorkspaceService.updateDocument(id, payload),
    onSuccess: () => {
      invalidate();
      toast.success("Documento atualizado.");
    },
    onError: () => toast.error("Não foi possível atualizar o documento."),
  });
  const archive = useMutation({
    mutationFn: (id: number) => recordWorkspaceService.archiveDocument(id),
    onSuccess: () => {
      invalidate();
      toast.success("Documento arquivado.");
    },
    onError: () => toast.error("Não foi possível arquivar o documento."),
  });
  return { upload, update, archive };
}
