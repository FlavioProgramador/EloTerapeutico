export type OrganizationType = "individual" | "clinic" | "company";
export type OrganizationStatus = "active" | "suspended" | "archived";
export type OnboardingStatus = "pending" | "in_progress" | "completed";
export type MembershipRole =
  | "owner"
  | "admin"
  | "therapist"
  | "receptionist"
  | "finance"
  | "viewer";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  legal_name: string;
  organization_type: OrganizationType;
  document: string;
  email: string;
  phone: string;
  timezone: string;
  status: OrganizationStatus;
  onboarding_status: OnboardingStatus;
  onboarding_step: number;
  onboarding_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMembership {
  id: number;
  organization: string;
  user_id: number;
  user_name: string;
  user_email: string;
  role: MembershipRole;
  status: "invited" | "active" | "suspended" | "revoked";
  is_default: boolean;
  joined_at: string | null;
}

export interface OrganizationContextPayload {
  active_organization: Organization | null;
  active_membership: OrganizationMembership | null;
  organizations: Organization[];
}

export const membershipRoleLabels: Record<MembershipRole, string> = {
  owner: "Proprietário",
  admin: "Administrador",
  therapist: "Terapeuta",
  receptionist: "Recepção",
  finance: "Financeiro",
  viewer: "Somente leitura",
};
