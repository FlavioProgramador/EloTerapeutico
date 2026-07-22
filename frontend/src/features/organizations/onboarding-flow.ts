import type { OrganizationOnboardingForm } from "./schemas/onboarding";
import type { Organization, OrganizationMembership } from "./types";

export interface OrganizationOnboardingPayload {
  organization: Organization;
  membership: OrganizationMembership;
  settings: Record<string, unknown>;
  professional_profile: Record<string, unknown> | null;
  status: string;
  step: number;
  completed_at: string | null;
}

export type OnboardingFormField = keyof OrganizationOnboardingForm;

export const organizationOnboardingDefaults: OrganizationOnboardingForm = {
  name: "",
  organization_type: "individual",
  legal_name: "",
  document: "",
  email: "",
  phone: "",
  timezone: "America/Sao_Paulo",
  display_name: "",
  professional_title: "",
  council_type: "",
  council_number: "",
  council_region: "",
  specialties_text: "",
  bio: "",
  public_email: "",
  professional_phone: "",
  default_appointment_duration: 50,
  default_session_value: 0,
  accepts_online: true,
  accepts_in_person: true,
  minimum_booking_notice_minutes: 0,
  maximum_booking_days: 90,
  cancellation_notice_hours: 24,
  allow_online_booking: false,
  allow_patient_portal: false,
  send_appointment_reminders: true,
  reminder_hours_before: 24,
  business_name_on_documents: "",
  document_header: "",
  document_footer: "",
};

const stepFields: Partial<Record<number, readonly OnboardingFormField[]>> = {
  1: [
    "name",
    "organization_type",
    "legal_name",
    "document",
    "email",
    "phone",
    "timezone",
  ],
  2: [
    "display_name",
    "professional_title",
    "council_type",
    "council_number",
    "council_region",
    "specialties_text",
    "bio",
    "public_email",
    "professional_phone",
  ],
  3: [
    "default_appointment_duration",
    "default_session_value",
    "minimum_booking_notice_minutes",
    "maximum_booking_days",
    "cancellation_notice_hours",
  ],
  4: [
    "reminder_hours_before",
    "business_name_on_documents",
    "document_header",
    "document_footer",
  ],
};

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function readNumber(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function readBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

export function normalizeOnboardingStep(step: unknown): number {
  const parsed = Number(step);
  if (!Number.isFinite(parsed)) return 1;
  return Math.min(Math.max(Math.trunc(parsed), 1), 6);
}

export function getOnboardingStepFields(
  step: number,
): OnboardingFormField[] {
  return [...(stepFields[step] ?? [])];
}

export function onboardingPayloadToForm(
  payload: OrganizationOnboardingPayload,
  user?: { full_name?: string; email?: string } | null,
): OrganizationOnboardingForm {
  const profile = payload.professional_profile ?? {};
  const settings = payload.settings ?? {};
  const specialties = Array.isArray(profile.specialties)
    ? profile.specialties.filter(
        (item): item is string =>
          typeof item === "string" && Boolean(item.trim()),
      )
    : [];

  return {
    ...organizationOnboardingDefaults,
    name: payload.organization.name,
    organization_type: payload.organization.organization_type,
    legal_name: payload.organization.legal_name,
    document: payload.organization.document,
    email: payload.organization.email,
    phone: payload.organization.phone,
    timezone: payload.organization.timezone,
    display_name: readString(profile.display_name, user?.full_name ?? ""),
    professional_title: readString(profile.professional_title),
    council_type: readString(profile.council_type),
    council_number: readString(profile.council_number),
    council_region: readString(profile.council_region),
    specialties_text: specialties.join(", "),
    bio: readString(profile.bio),
    public_email: readString(profile.public_email, user?.email ?? ""),
    professional_phone: readString(profile.phone),
    default_appointment_duration: readNumber(
      profile.default_appointment_duration,
      50,
    ),
    default_session_value: readNumber(profile.default_session_value, 0),
    accepts_online: readBoolean(profile.accepts_online, true),
    accepts_in_person: readBoolean(profile.accepts_in_person, true),
    minimum_booking_notice_minutes: readNumber(
      settings.minimum_booking_notice_minutes,
      0,
    ),
    maximum_booking_days: readNumber(settings.maximum_booking_days, 90),
    cancellation_notice_hours: readNumber(
      settings.cancellation_notice_hours,
      24,
    ),
    allow_online_booking: readBoolean(settings.allow_online_booking, false),
    allow_patient_portal: readBoolean(settings.allow_patient_portal, false),
    send_appointment_reminders: readBoolean(
      settings.send_appointment_reminders,
      true,
    ),
    reminder_hours_before: readNumber(settings.reminder_hours_before, 24),
    business_name_on_documents: readString(
      settings.business_name_on_documents,
      payload.organization.name,
    ),
    document_header: readString(settings.document_header),
    document_footer: readString(settings.document_footer),
  };
}

export function buildOnboardingStepPayload(
  step: number,
  data: OrganizationOnboardingForm,
): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    step: normalizeOnboardingStep(step + 1),
  };

  if (step === 1) {
    payload.organization = {
      name: data.name,
      organization_type: data.organization_type,
      legal_name: data.legal_name,
      document: data.document,
      email: data.email,
      phone: data.phone,
      timezone: data.timezone,
    };
  } else if (step === 2 || step === 3) {
    payload.professional_profile = {
      display_name: data.display_name,
      professional_title: data.professional_title,
      council_type: data.council_type,
      council_number: data.council_number,
      council_region: data.council_region,
      specialties: data.specialties_text
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      bio: data.bio,
      phone: data.professional_phone,
      public_email: data.public_email,
      default_appointment_duration: data.default_appointment_duration,
      default_session_value: data.default_session_value,
      accepts_online: data.accepts_online,
      accepts_in_person: data.accepts_in_person,
    };
  } else if (step === 4) {
    payload.settings = {
      default_timezone: data.timezone,
      default_appointment_duration: data.default_appointment_duration,
      minimum_booking_notice_minutes: data.minimum_booking_notice_minutes,
      maximum_booking_days: data.maximum_booking_days,
      cancellation_notice_hours: data.cancellation_notice_hours,
      allow_online_booking: data.allow_online_booking,
      allow_patient_portal: data.allow_patient_portal,
      allow_telemedicine: false,
      send_appointment_reminders: data.send_appointment_reminders,
      reminder_hours_before: data.reminder_hours_before,
      business_name_on_documents: data.business_name_on_documents,
      document_header: data.document_header,
      document_footer: data.document_footer,
    };
  }

  return payload;
}
