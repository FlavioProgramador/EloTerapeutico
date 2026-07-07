import { api } from "@/lib/api";

import type { AppointmentsReport, PatientsReport, ReportTab } from "./types";

export type ReportParams = Record<string, string | number | undefined>;

const endpoints: Record<ReportTab, string> = {
  appointments: "reports/appointments/",
  patients: "reports/patients/",
  financial: "reports/financial/",
  "online-scheduling": "reports/online-scheduling/",
};

export const reportsService = {
  appointments: async (params: ReportParams) => {
    const response = await api.get<AppointmentsReport>(endpoints.appointments, { params });
    return response.data;
  },
  patients: async (params: ReportParams) => {
    const response = await api.get<PatientsReport>(endpoints.patients, { params });
    return response.data;
  },
  byTab: async (tab: ReportTab, params: ReportParams) => {
    const response = await api.get(endpoints[tab], { params });
    return response.data;
  },
  download: async (tab: ReportTab, format: "csv" | "pdf", params: ReportParams) => {
    const response = await api.get("reports/export/", {
      params: { ...params, type: tab, format },
      responseType: "blob",
    });
    return response.data as Blob;
  },
};
