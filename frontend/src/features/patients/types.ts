export type PatientStatus = string;
export type PatientDashboardItem = Record<"id", number> & Record<string, string | number | boolean | null | string[]>;
export type PatientMetrics = Record<string, number>;
export type PatientPanelData = Record<string, unknown>;
