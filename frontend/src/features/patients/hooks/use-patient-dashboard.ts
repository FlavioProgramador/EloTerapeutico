import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { PatientMetrics } from "../types";

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
