export interface SettingsProfile {
  id: number;
  email: string;
  full_name: string;
  display_name: string;
  profession: string;
  role: "therapist" | "secretary" | "admin";
  specialty: string;
  crp_number: string;
  bio: string;
  phone: string;
  avatar: string | null;
  clinic_name: string;
  professional_address: Record<string, string>;
  default_session_duration: number;
  default_session_value: string;
  default_modality: "in_person" | "online" | "hybrid";
  timezone: string;
  language: string;
  date_format: string;
  time_format: string;
  date_joined: string;
  last_login: string | null;
}

export interface PracticeSettings {
  trade_name: string;
  document: string;
  phone: string;
  email: string;
  address: Record<string, string>;
  timezone: string;
  currency: string;
  appointment_interval_minutes: number;
  minimum_booking_notice_hours: number;
  cancellation_notice_hours: number;
  allow_overbooking: boolean;
  consider_holidays: boolean;
  reminders_enabled: boolean;
  reminder_minutes: number;
  internal_communications_enabled: boolean;
  message_preview_enabled: boolean;
  auto_mark_read: boolean;
  mentions_enabled: boolean;
  notify_mentions: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  communication_policy: string;
  updated_at: string;
}

export interface WorkingHour {
  id: number;
  weekday: number;
  weekday_display: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface AuthSessionItem {
  public_id: string;
  user_agent: string;
  created_at: string;
  last_seen_at: string;
  expires_at: string;
  is_current: boolean;
}
