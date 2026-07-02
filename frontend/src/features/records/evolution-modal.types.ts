export type EvolutionContentFormat = "markdown" | "plain_text";

export interface EvolutionAppointmentOption {
  id: number;
  patient: number;
  patient_name: string;
  therapist: number;
  therapist_name: string;
  start_time: string;
  end_time: string;
  status: string;
  status_display: string;
  modality: string;
  modality_display: string;
  appointment_type: string;
  type_display: string;
}

export interface ClinicalEvolutionTemplate {
  id: number;
  name: string;
  content: string;
  owner: number | null;
  owner_name: string | null;
  is_system: boolean;
  is_active: boolean;
}

export interface EvolutionAttachment {
  id: number;
  original_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
  download_url: string;
  preview_url: string | null;
}

export interface PendingEvolutionAttachment {
  id: string;
  file: File;
  previewUrl?: string;
  progress: number;
  error?: string;
}

export interface EvolutionModalPayload {
  appointment?: number | null;
  session_date: string;
  content: string;
  therapist_observations: string;
  content_format: EvolutionContentFormat;
  is_confidential: boolean;
  confirm_appointment_date_override?: boolean;
}
