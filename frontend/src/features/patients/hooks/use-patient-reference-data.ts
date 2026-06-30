"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { PatientMetrics } from "../types";
import {
  buildPatientListParams,
  type PatientListFilters,
  type PatientPageData,
} from "../components/patient-list-config";
import type { PatientListItem } from "../components/patient-list-item";

interface Options {
  params: URLSearchParams;
  search: string;
  filters: PatientListFilters;
  birthdaysOnly: boolean;
  pageSize: number;
}

export function usePatientReferenceData({
  params,
  search,
  filters,
  birthdaysOnly,
  pageSize,
}: Options) {
  const queryClient = useQueryClient();
  const [exporting, setExporting] = useState(false);

  const list = useQuery({
    queryKey: ["patients", "reference-list", params.toString()],
    queryFn: () =>
      api
        .get<PatientPageData>(`patients/?${params.toString()}`)
        .then((response) => response.data),
    placeholderData: (previous) => previous,
  });

  const metrics = useQuery({
    queryKey: ["patients", "dashboard-metrics"],
    queryFn: () =>
      api
        .get<PatientMetrics>("patients/dashboard-metrics/")
        .then((response) => response.data),
  });

  const birthdayCount = useQuery({
    queryKey: ["patients", "birthday-count"],
    queryFn: () =>
      api
        .get<PatientPageData>("patients/?birthdays=true&page=1&page_size=1")
        .then((response) => response.data.pagination.count),
  });

  const refreshList = () =>
    queryClient.invalidateQueries({
      queryKey: ["patients", "reference-list"],
    });

  const reminder = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      api.patch(`patients/${id}/reminders/`, { enabled }),
    onSuccess: async (_, values) => {
      await refreshList();
      toast.success(
        values.enabled ? "Lembretes ativados." : "Lembretes desativados.",
      );
    },
    onError: () => toast.error("Não foi possível atualizar os lembretes."),
  });

  const archive = useMutation({
    mutationFn: (id: number) => api.delete(`patients/${id}/`),
    onSuccess: async () => {
      await Promise.all([
        refreshList(),
        queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        }),
      ]);
      toast.success("Paciente arquivado com sucesso.");
    },
    onError: () => toast.error("Não foi possível arquivar o paciente."),
  });

  const restore = useMutation({
    mutationFn: (id: number) => api.post(`patients/${id}/restore/`),
    onSuccess: async () => {
      await Promise.all([
        refreshList(),
        queryClient.invalidateQueries({
          queryKey: ["patients", "dashboard-metrics"],
        }),
      ]);
      toast.success("Paciente restaurado com sucesso.");
    },
    onError: () => toast.error("Não foi possível restaurar o paciente."),
  });

  const exportCsv = async () => {
    try {
      setExporting(true);
      const exportParams = buildPatientListParams(
        search,
        filters,
        1,
        pageSize,
        birthdaysOnly,
      );
      exportParams.delete("page");
      exportParams.delete("page_size");
      const response = await api.get(
        `patients/export-csv/?${exportParams.toString()}`,
        { responseType: "blob" },
      );
      const objectUrl = URL.createObjectURL(response.data as Blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = "pacientes.csv";
      link.click();
      URL.revokeObjectURL(objectUrl);
      toast.success("Exportação concluída.");
    } catch {
      toast.error("Não foi possível exportar os pacientes.");
    } finally {
      setExporting(false);
    }
  };

  const archivePatient = (patient: PatientListItem) => {
    const confirmed = window.confirm(
      `Arquivar o cadastro de ${patient.display_name}? O histórico será preservado.`,
    );
    if (confirmed) archive.mutate(patient.id);
  };

  return {
    list,
    metrics,
    birthdayCount,
    reminder,
    archive,
    restore,
    exporting,
    exportCsv,
    archivePatient,
  };
}
