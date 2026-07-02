export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "completed"
  | "missed"
  | "cancelled"
  | "rescheduled";

export type AppointmentModality = "in_person" | "online" | "hybrid";
export type AppointmentType =
  | "assessment"
  | "psychotherapy"
  | "follow_up"
  | "guidance"
  | "group"
  | "other";

export interface AgendaPagination {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
}

export interface PaginatedAgendaResponse<T> {
  pagination: AgendaPagination;
  results: T[];
}

export interface AgendaAppointment {
  id: number;
  patient: number;
  patient_name: string;
  therapist: number;
  therapist_name: string;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  duration_display: string;
  status: AppointmentStatus;
  status_display: string;
  modality: AppointmentModality;
  modality_display: string;
  appointment_type: AppointmentType;
  type_display: string;
  room: number | null;
  room_name: string | null;
  session_value: string;
  is_recurring: boolean;
  recurrence: number | null;
  package: number | null;
  telemedicine_status: string | null;
  notes?: string;
  cancellation_reason?: string;
  telemedicine?: TelemedicineRoom | null;
}

export interface AppointmentFilters {
  search?: string;
  date?: string;
  start_time_gte?: string;
  start_time_lte?: string;
  patient?: number;
  therapist?: number;
  room?: number;
  status?: string;
  modality?: string;
  appointment_type?: string;
  recurring?: boolean;
  telemedicine?: boolean;
  pending_only?: boolean;
  confirmed_only?: boolean;
  page?: number;
  page_size?: number;
}

export interface CreateAppointmentPayload {
  patient: number;
  participants?: number[];
  therapist?: number;
  start_time: string;
  end_time: string;
  modality: AppointmentModality;
  appointment_type: AppointmentType;
  room?: number | null;
  session_value: string;
  notes?: string;
  package?: number | null;
  send_whatsapp_reminder?: boolean;
  is_recurring?: boolean;
  recurrence_frequency?: "weekly" | "biweekly" | "monthly" | "custom";
  recurrence_interval?: number;
  recurrence_weekdays?: number[];
  recurrence_ends_on?: string | null;
  recurrence_max_occurrences?: number;
  recurrence_conflict_strategy?: "error" | "skip";
}

export interface TimeSlot {
  start: string;
  end: string;
  start_datetime: string;
  end_datetime: string;
}

export interface AgendaRoom {
  id: number;
  therapist: number;
  therapist_name: string;
  name: string;
  location: string;
  capacity: number;
  is_active: boolean;
}

export interface ScheduleBlock {
  id: number;
  therapist: number;
  therapist_name: string;
  start_time: string;
  end_time: string;
  reason: string;
  notes: string;
  is_active: boolean;
  recurrence_rule: string;
  affected_appointments: number;
}

export interface CreateScheduleBlockPayload {
  therapist?: number;
  start_time: string;
  end_time: string;
  reason: string;
  notes?: string;
  recurrence_rule?: string;
  confirm_conflicts?: boolean;
}

export interface AppointmentRecurrence {
  id: number;
  patient: number;
  patient_name: string;
  therapist: number;
  therapist_name: string;
  frequency: string;
  frequency_display: string;
  interval: number;
  weekdays: number[];
  starts_on: string;
  ends_on: string | null;
  max_occurrences: number | null;
  start_time: string;
  duration_minutes: number;
  modality: AppointmentModality;
  appointment_type: AppointmentType;
  room: number | null;
  session_value: string;
  notes: string;
  status: "active" | "paused" | "ended";
  occurrences_count: number;
  completed_count: number;
  next_occurrence_id: number | null;
  next_occurrence_at: string | null;
  created_at: string;
}

export interface PackageSession {
  id: number;
  appointment: number | null;
  appointment_status: string | null;
  scheduled_for: string;
  status: string;
  consumed: boolean;
}

export interface PatientPackage {
  id: number;
  patient: number;
  patient_name: string;
  therapist: number;
  therapist_name: string;
  name: string;
  description: string;
  sessions_contracted: number;
  sessions_used: number;
  remaining_sessions: number;
  total_value: string;
  unit_value: string;
  valid_from: string;
  valid_until: string | null;
  status: string;
  is_expired: boolean;
  generate_charge: boolean;
  send_charge: boolean;
  sessions: PackageSession[];
  created_at: string;
}

export interface CreatePackagePayload {
  patient: number;
  therapist?: number;
  name: string;
  description?: string;
  sessions_contracted: number;
  total_value: string;
  valid_from?: string;
  valid_until?: string | null;
  generate_charge?: boolean;
  send_charge?: boolean;
  auto_schedule?: boolean;
  first_appointment_at?: string;
  frequency?: string;
  weekdays?: number[];
  duration_minutes?: number;
  modality?: AppointmentModality;
  appointment_type?: AppointmentType;
  room?: number | null;
  send_whatsapp_reminder?: boolean;
}

export interface TelemedicineRoom {
  id: number;
  appointment: number;
  appointment_start: string;
  patient_name: string;
  therapist_name: string;
  patient_link: string;
  professional_link: string;
  expires_at: string;
  status: string;
  is_accessible: boolean;
}
