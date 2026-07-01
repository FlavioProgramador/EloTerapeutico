import type { Patient } from "@/types";

export type RecordTab = "evolutions" | "appointments" | "documents" | "forms" | "exports";
export type EvolutionStatus = "draft" | "finalized" | "archived";
export type EvolutionModality = "in_person" | "online" | "hybrid";
export type AppointmentType = "individual" | "couple" | "family" | "group" | "other";

export interface RecordSummary {
  patient: Pick<Patient, "id" | "full_name" | "age" | "phone" | "email" | "status" | "created_at" | "updated_at"> & {
    status_display: string;
  };
  sessions_total: number;
  treatment_start: string;
  last_update: string;
  latest_evolution_id: number | null;
  last_session: string | null;
  next_session: {
    id: number;
    start_time: string;
    end_time: string;
    duration_minutes: number;
    status: string;
  } | null;
  goals: TreatmentGoal[];
  recent_documents: ClinicalDocument[];
  ai_summary: {
    available: boolean;
    enabled: boolean;
    message: string;
  };
}

export interface EvolutionWorkspace {
  id: number;
  patient: number;
  appointment?: number | null;
  session_date: string;
  session_time?: string | null;
  duration_minutes: number;
  modality: EvolutionModality;
  appointment_type: AppointmentType;
  emotional_state: string;
  chief_complaint: string;
  patient_report: string;
  therapist_observations: string;
  interventions: string;
  perceived_evolution: string;
  homework: string;
  referrals: string;
  next_steps: string;
  content: string;
  cid10?: string;
  status: EvolutionStatus;
  status_display: string;
  is_locked: boolean;
  locked_at: string | null;
  is_editable: boolean;
  addenda_count: number;
  attached_documents_count?: number;
  linked_goal_ids?: number[];
  version_count: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  finalized_at?: string | null;
  archived_at?: string | null;
}

export interface EvolutionPayload {
  appointment?: number | null;
  session_date: string;
  session_time?: string | null;
  duration_minutes?: number;
  modality?: EvolutionModality;
  appointment_type?: AppointmentType;
  emotional_state?: string;
  chief_complaint?: string;
  patient_report?: string;
  therapist_observations?: string;
  interventions?: string;
  perceived_evolution?: string;
  homework?: string;
  referrals?: string;
  next_steps?: string;
  content?: string;
  cid10?: string;
}

export interface AnamnesisWorkspace {
  exists?: boolean;
  id?: number;
  patient: number;
  chief_complaint?: string;
  reason_for_care?: string;
  history?: string;
  family_history?: string;
  physical_health_history?: string;
  mental_health_history?: string;
  medications?: string;
  previous_treatments?: string;
  habits_and_routine?: string;
  sleep?: string;
  nutrition?: string;
  family_social_relations?: string;
  academic_history?: string;
  professional_history?: string;
  support_network?: string;
  relevant_events?: string;
  initial_assessment?: string;
  clinical_hypotheses?: string;
  observations?: string;
  custom_fields?: string;
  completion_percentage: number;
  version_count: number;
  status?: "draft" | "complete";
  status_display?: string;
  updated_by_name?: string;
  created_at?: string;
  updated_at?: string;
}

export type GoalStatus = "active" | "paused" | "completed" | "archived";
export type GoalPriority = "low" | "medium" | "high";

export interface TreatmentGoal {
  id: number;
  patient: number;
  title: string;
  description: string;
  category: string;
  priority: GoalPriority;
  priority_display: string;
  start_date: string;
  target_date?: string | null;
  status: GoalStatus;
  status_display: string;
  progress: number;
  strategies: string;
  evaluation_criteria: string;
  observations: string;
  sort_order: number;
  evolutions: number[];
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ClinicalDocument {
  id: number;
  patient: number;
  evolution?: number | null;
  evolution_date?: string | null;
  category: string;
  category_display: string;
  original_name: string;
  description: string;
  content_type: string;
  size_bytes: number;
  version: number;
  is_archived: boolean;
  status?: "available" | "archived";
  status_display?: string;
  uploaded_by_name?: string;
  created_at: string;
  updated_at: string;
  download_url: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
