export type PatientStatus = "active" | "inactive" | "archived";
export type PatientDashboardItem = Record<"id", number> & Record<"full_name", string>;
