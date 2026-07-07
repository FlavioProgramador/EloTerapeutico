export type ReportTab = "appointments" | "patients" | "financial" | "online-scheduling";

export interface PeriodPayload {
  start_date: string;
  end_date: string;
}

export interface ChartPoint {
  label: string;
  value: number;
  key?: string;
  month?: string;
}

export interface MonthlyEvolutionPoint {
  month: string;
  label: string;
  completed: number;
  cancelled: number;
  missed: number;
}

export interface ReportTable<T> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
}

export interface AppointmentRow {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  patient: string;
  professional: string;
  status: string;
  status_display: string;
  room: string;
  insurance: string;
  amount: number;
}

export interface AppointmentsReport {
  period: PeriodPayload;
  kpis: {
    total: number;
    attendance_rate: number;
    cancellation_rate: number;
    miss_rate: number;
  };
  charts: {
    status_distribution: ChartPoint[];
    by_room: ChartPoint[];
    by_insurance: ChartPoint[];
    busy_hours: ChartPoint[];
    monthly_evolution: MonthlyEvolutionPoint[];
  };
  table: ReportTable<AppointmentRow>;
}

export interface PatientRiskRow {
  id: number;
  patient: string;
  professional: string;
  last_appointment: string | null;
  next_appointment: string | null;
  days_without_appointment: number;
  status: string;
  status_display: string;
  contact: string | null;
}

export interface PatientsReport {
  period: PeriodPayload;
  kpis: {
    active_patients: number;
    new_patients: number;
    evasion_risk: number;
    retention_rate: number;
  };
  charts: {
    new_patients_by_month: ChartPoint[];
    active_vs_inactive: ChartPoint[];
    patients_by_professional: ChartPoint[];
    age_distribution: ChartPoint[];
  };
  risk: ReportTable<PatientRiskRow>;
}
