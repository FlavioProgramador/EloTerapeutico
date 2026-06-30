import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PatientDashboardPage, SafePatientPanelData } from "../panel-contracts";
import type { PatientMetrics } from "../types";

export interface PatientPageFilters {
  search?: string;
  status?: string;
  modality?: string;
  payerType?: string;
  tag?: string;
  noNextSession?: boolean;
  page?: number;
  pageSize?: number;
}

function queryString(filters: PatientPageFilters) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.status) params.set("status", filters.status);
  if (filters.modality) params.set("modality", filters.modality);
  if (filters.payerType) params.set("payer_type", filters.payerType);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.noNextSession) params.set("no_next_session", "true");
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("page_size", String(filters.pageSize));
  return params.toString();
}

export function usePatientPage(filters: PatientPageFilters) {
  return useQuery({
    queryKey: ["patients", "page", filters],
    queryFn: async () => {
      const response = await api.get<PatientDashboardPage>(
        `patients/?${queryString(filters)}`,
      );
      return response.data;
    },
  });
}

export function usePatientPageMetrics() {
  return useQuery({
    queryKey: ["patients", "dashboard-metrics"],
    queryFn: async () => {
      const response = await api.get<PatientMetrics>("patients/dashboard-metrics/");
      return response.data;
    },
  });
}

export function usePatientPagePanel(patientId?: number) {
  return useQuery({
    queryKey: ["patients", patientId, "dashboard"],
    queryFn: async () => {
      const response = await api.get<SafePatientPanelData>(
        `patients/${patientId}/dashboard/`,
      );
      return response.data;
    },
    enabled: Boolean(patientId),
  });
}

export async function downloadPatientCsv(filters: PatientPageFilters) {
  const response = await api.get(`patients/export-csv/?${queryString(filters)}`, {
    responseType: "blob",
  });
  return response.data as Blob;
}
