import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PaginatedResponse } from "@/types";
import type {
  PatientDashboardItem,
  PatientMetrics,
  PatientPanelData,
} from "../types";

export interface PatientDashboardFilters {
  search?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}

export function usePatientDashboardList(filters: PatientDashboardFilters) {
  return useQuery({
    queryKey: ["patients", "dashboard-list", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.search) params.set("search", filters.search);
      if (filters.status) params.set("status", filters.status);
      if (filters.page) params.set("page", String(filters.page));
      if (filters.pageSize) params.set("page_size", String(filters.pageSize));
      const response = await api.get<PaginatedResponse<PatientDashboardItem>>(
        `patients/?${params.toString()}`,
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
