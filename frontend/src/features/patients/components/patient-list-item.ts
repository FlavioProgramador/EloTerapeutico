import type { PatientDashboardItem } from "../types";

export type PatientListItem = PatientDashboardItem & {
  birth_date?: string | null;
  reminders_enabled?: boolean;
};
