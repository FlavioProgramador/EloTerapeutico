import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PatientMetrics, PatientPanelData } from "../types";

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
    queryFn: () => api.get<PatientPanelData>(`patients/${patientId}/dashboard/`).then((response) => response.data),
    enabled: Boolean(patientId),
  });
}
