export type CommunicationChannel =
  | "in_app"
  | "email"
  | "whatsapp_manual"
  | "whatsapp"
  | "sms";
export type CommunicationStatus =
  | "draft"
  | "scheduled"
  | "queued"
  | "processing"
  | "sent"
  | "delivered"
  | "read"
  | "responded"
  | "failed"
  | "canceled"
  | "expired";
export type ChannelConnectionStatus =
  | "not_configured"
  | "incomplete"
  | "validating"
  | "configured"
  | "error"
  | "disabled"
  | "unavailable";
export type ChannelOperationalStatus =
  | "active"
  | "inactive"
  | "validating"
  | "error"
  | "unavailable";

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
export interface Communication {
  public_id: string;
  patient: number | null;
  patient_name: string;
  category: string;
  channel: CommunicationChannel;
  subject: string;
  status: CommunicationStatus;
  priority: "low" | "normal" | "high";
  scheduled_at: string | null;
  sent_at: string | null;
  created_at: string;
  created_by_name: string;
  recipient: string;
  source_event: string;
}
export interface CommunicationDetail extends Communication {
  appointment: number | null;
  body: string;
  body_html: string;
  template: number | null;
  template_name: string;
  queued_at: string | null;
  processing_started_at: string | null;
  delivered_at: string | null;
  failed_at: string | null;
  canceled_at: string | null;
  provider_name: string;
  metadata: Record<string, unknown>;
  recipients: Array<{
    id: number;
    recipient_type: string;
    name: string;
    destination_masked: string;
    channel: string;
    status: string;
    blocked_reason: string;
  }>;
  attempts: Array<{
    id: number;
    attempt_number: number;
    provider: string;
    status: string;
    error_message: string;
    started_at: string | null;
    finished_at: string | null;
    next_retry_at: string | null;
  }>;
}
export interface CommunicationDashboard {
  period: { start: string; end: string };
  metrics: {
    total: number;
    scheduled: number;
    delivered: number;
    failed: number;
    appointment_confirmations: number;
    success_rate: number;
  };
  by_channel: Array<{ channel: CommunicationChannel; total: number }>;
  by_status: Array<{ status: CommunicationStatus; total: number }>;
  daily: Array<{ day: string; total: number }>;
}
export interface CommunicationTemplate {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  channel: CommunicationChannel;
  subject_template: string;
  body_template: string;
  allowed_variables: string[];
  is_system_template: boolean;
  is_active: boolean;
  is_archived: boolean;
  can_edit: boolean;
}
export interface CommunicationAutomation {
  id: number;
  name: string;
  description: string;
  event_type: string;
  channel: CommunicationChannel;
  template: number;
  template_name: string;
  is_active: boolean;
  delay_value: number;
  delay_unit: string;
  send_before_event: boolean;
  failures: number;
  last_run_at: string | null;
}

export type ChannelFieldKind =
  | "text"
  | "email"
  | "password"
  | "number"
  | "boolean"
  | "textarea"
  | "tel"
  | "url";
export interface ChannelConfigurationField {
  name: string;
  label: string;
  kind: ChannelFieldKind;
  required: boolean;
  secret?: boolean;
  read_only?: boolean;
  placeholder?: string;
  default?: string | number | boolean;
}
export interface ChannelProviderDefinition {
  id: string;
  label: string;
  description: string;
  instructions: string;
  fields: ChannelConfigurationField[];
  secret_fields: string[];
}
export interface CommunicationChannelConfig {
  channel: CommunicationChannel;
  provider: string;
  is_active: boolean;
  sender: string;
  public_identifier: string;
  connection_status: ChannelConnectionStatus;
  operational_status: ChannelOperationalStatus;
  last_validated_at: string | null;
  last_tested_at: string | null;
  last_error: { code: string; message: string } | null;
  metadata: Record<string, string | number | boolean>;
  credential_state: Record<string, boolean>;
  available_providers: ChannelProviderDefinition[];
  missing_fields: string[];
  configuration_complete: boolean;
  updated_at: string;
}
export interface UpdateChannelConfigurationPayload {
  provider: string;
  sender?: string;
  public_identifier?: string;
  metadata: Record<string, string | number | boolean>;
  secrets?: Record<string, string>;
  save_as_draft?: boolean;
  confirm_provider_change?: boolean;
}
export interface ChannelTestResponse {
  channel: CommunicationChannelConfig;
  test: {
    success: boolean;
    status: CommunicationStatus;
    external_id: string;
    metadata: {
      manual_url?: string;
      requires_confirmation?: boolean;
      provider_status?: string;
      price?: string | null;
      price_unit?: string | null;
    };
  };
}

export type NotificationCategory =
  | "agenda"
  | "patients"
  | "records"
  | "documents"
  | "financial"
  | "billing"
  | "communications"
  | "forms"
  | "security"
  | "system";

export interface InAppNotification {
  public_id: string;
  category: NotificationCategory;
  category_display: string;
  title: string;
  message: string;
  notification_type: string;
  priority: "low" | "normal" | "high" | "critical";
  priority_display: string;
  internal_url: string;
  action_label: string;
  metadata: Record<string, string | number | boolean | null>;
  is_read: boolean;
  read_at: string | null;
  archived_at: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface NotificationPreference {
  in_app_enabled: boolean;
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  timezone: string;
  category_preferences: Partial<
    Record<NotificationCategory, Partial<Record<"in_app" | "email" | "whatsapp" | "push", boolean>>>
  >;
  daily_digest_enabled: boolean;
  updated_at: string;
}

export interface NotificationCategoryOption {
  value: NotificationCategory;
  label: string;
}
export interface PatientOption {
  id: number;
  full_name: string;
  email?: string;
  whatsapp?: string;
  phone?: string;
}
export interface CreateCommunicationPayload {
  patient_id?: number | null;
  channel: CommunicationChannel;
  category: string;
  template_id?: number | null;
  subject?: string;
  body?: string;
  scheduled_at?: string | null;
  priority?: "low" | "normal" | "high";
  recipient_type?: "patient" | "guardian";
  draft?: boolean;
}
