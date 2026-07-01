import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { QUERY_KEYS } from "@/constants";
import type { PatientFormRequest } from "../types/patient-form.types";
import {
  patientsService,
  type PatientFilters,
} from "../services/patients.service";

export function usePatients(filters?: PatientFilters) {
  return useQuery({
    queryKey: [...QUERY_KEYS.patients, filters],
    queryFn: () => patientsService.list(filters),
  });
}

export function usePatient(id: number | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.patient(id ?? 0),
    queryFn: () => patientsService.getById(id as number),
    enabled: Boolean(id),
  });
}

export function usePatientProfessionals() {
  return useQuery({
    queryKey: ["patients", "professionals"],
    queryFn: patientsService.professionals,
  });
}

export function useCreatePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PatientFormRequest | FormData) =>
      patientsService.create(data),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "reference-list"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "birthday-count"],
        }),
      ]);
      toast.success("Paciente cadastrado com sucesso.");
    },
  });
}

export function useUpdatePatient(id: number | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PatientFormRequest | FormData) =>
      patientsService.update(id as number, data),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "reference-list"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        }),
        id
          ? queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patient(id) })
          : Promise.resolve(),
      ]);
      toast.success("Paciente atualizado com sucesso.");
    },
  });
}

export function useDeletePatient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: patientsService.delete,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "reference-list"],
        }),
        queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        }),
      ]);
      toast.success("Paciente arquivado com sucesso.");
    },
    onError: () => toast.error("Não foi possível arquivar o paciente."),
  });
}
