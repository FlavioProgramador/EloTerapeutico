import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type {
  PatientDashboardItem,
  PatientMetrics,
  PatientPanelData,
} from "../types";

export interface PatientDashboardFilters {
  search?: string;
  status?: string;
  modality?: string;
  payerType?: string;
  tag?: string;
  noNextSession?: boolean;
  page?: number;
  pageSize?: number;
  ordering?: string;
}

export interface PatientDashboardResponse {
  pagination: {
    count: number;
    total_pages: number;
    current_page: number;
    next?: string | null;
    previous?: string | null;
  };
  results: PatientDashboardItem[];
}

function buildParams(filters: PatientDashboardFilters) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.status) params.set("status", filters.status);
  if (filters.modality) params.set("modality", filters.modality);
  if (filters.payerType) params.set("payer_type", filters.payerType);
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.noNextSession) params.set("no_next_session", "true");
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("page_size", String(filters.pageSize));
  if (filters.ordering) params.set("ordering", filters.ordering);
  return params;
}

export function usePatientDashboardList(filters: PatientDashboardFilters) {
  return useQuery({
    queryKey: ["patients", "dashboard-list", filters],
    queryFn: async () => {
      const response = await api.get<PatientDashboardResponse>(
        `patients/?${buildParams(filters).toString()}`,
      );
      return response.data;
    },
  });
}

export function usePatientMetrics() {
  return useQuery({
    queryKey: ["patients", "dashboard-metrics"],
    queryFn: async () => {
      const response = await api.get<PatientMetrics>(
        "patients/dashboard-metrics/",
      );
      return response.data;
    },
  });
}

export function usePatientPanel(patientId?: number) {
  return useQuery({
    queryKey: ["patients", patientId, "dashboard"],
    queryFn: () =>
      api
        .get<PatientPanelData>(`patients/${patientId}/dashboard/`)
        .then((response) => response.data),
    enabled: Boolean(patientId),
  });
}

export async function exportPatientsCsv(filters: PatientDashboardFilters) {
  const response = await api.get(
    `patients/export-csv/?${buildParams(filters).toString()}`,
    { responseType: "blob" },
  );
  return response.data as Blob;
}
