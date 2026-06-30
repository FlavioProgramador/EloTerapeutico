import type { PatientDashboardItem } from "./types";

export interface PatientDashboardPage {
  pagination: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  results: PatientDashboardItem[];
}

export interface SafePatientPanelData {
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
  ai_summary: {
    available: boolean;
    message: string;
  };
}
