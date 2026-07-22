export type TelemedicineRole = "patient" | "professional";

export interface TelemedicineInvitationStatus {
  status: "missing" | "valid" | "expired";
  expires_at: string | null;
  last_used_at: string | null;
}

export interface TelemedicineParticipant {
  role: TelemedicineRole;
  provider_participant_identity: string;
  joined_at: string;
}

export interface TelemedicineDashboardRoom {
  id: number;
  public_id: string;
  appointment: number;
  appointment_start: string;
  appointment_end: string;
  modality: "online" | "hybrid";
  patient_name: string;
  therapist_name: string;
  expires_at: string;
  status:
    | "pending"
    | "available"
    | "waiting"
    | "in_progress"
    | "finished"
    | "cancelled"
    | "expired"
    | "failed";
  is_accessible: boolean;
  e2ee_enabled: boolean;
  started_at: string | null;
  ended_at: string | null;
  patient_joined_at: string | null;
  professional_joined_at: string | null;
  last_participant_left_at: string | null;
  invitation_status: TelemedicineInvitationStatus;
  active_participants: TelemedicineParticipant[];
  created_at: string;
  updated_at: string;
}

export interface TelemedicinePublicContext {
  room_public_id: string;
  organization_name: string;
  therapist_name: string;
  appointment_start: string;
  appointment_end: string;
  room_status: string;
  invitation_expires_at: string;
  consent_version: string;
  consent_text: string;
  consent_accepted: boolean;
  recording_enabled: false;
  e2ee_required: boolean;
}

export interface TelemedicineCredentials {
  server_url: string;
  token: string;
  identity: string;
  room_name: string;
  role: TelemedicineRole;
  e2ee_key: string;
  e2ee_enabled: boolean;
  expires_in: number;
  recording_enabled: false;
}

export interface TelemedicineDeviceChoices {
  username: string;
  audioEnabled: boolean;
  videoEnabled: boolean;
  audioDeviceId: string;
  videoDeviceId: string;
}
