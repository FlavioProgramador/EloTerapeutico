export type PatientStatus =
  | "active"
  | "evaluation"
  | "waiting_return"
  | "discharged"
  | "inactive"
  | "archived";

export interface PatientDashboardItem {
  id: number;
  full_name: string;
  social_name?: string;
  display_name: string;
  masked_cpf: string;
  age?: number;
  phone?: string;
  whatsapp?: string;
  email?: string;
  status: PatientStatus;
  status_display: string;
  tags: string[];
  therapist: number;
  therapist_name: string;
  attendance_type: string;
  modality: string;
  payer_type: string;
  insurance_name?: string;
  last_session?: string | null;
  next_session?: string | null;
  next_session_status?: string | null;
  latest_evolution_at?: string | null;
  latest_evolution_id?: number | null;
  total_sessions: number;
  missed_sessions: number;
  documents_count: number;
  active_goals_count: number;
  has_anamnesis: boolean;
  created_at: string;
  updated_at: string;
}

export interface PatientMetrics {
  total: number;
  active: number;
  active_percentage: number;
  discharged: number;
  discharged_percentage: number;
  new_current_month: number;
  new_previous_month: number;
}

export interface PatientPanelData {
  patient: PatientDashboardItem;
  can_access_records: boolean;
  next_session: null | {
    id: number;
    start_time: string;
    end_time: string;
    status: string;
  };
  latest_evolution: null | {
    id: number;
    session_date: string;
    summary: string;
    is_locked: boolean;
  };
  recent_documents: Array<{
    id: number;
    name: string;
    category: string;
    created_at: string;
  }>;
  follow_up: {
    total_sessions: number;
    missed_sessions: number;
    attendance_percentage: number | null;
    active_goals: number;
  };
  ai_summary: { available: boolean; message: string };
}
