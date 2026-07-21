import { z } from "zod";

export const organizationOnboardingSchema = z.object({
  name: z.string().trim().min(2, "Informe o nome do consultório ou clínica."),
  organization_type: z.enum(["individual", "clinic", "company"]),
  legal_name: z.string().trim().max(200),
  document: z.string().trim().max(32),
  email: z.string().trim().email("Informe um e-mail válido.").or(z.literal("")),
  phone: z.string().trim().max(24),
  timezone: z.string().trim().min(1),
  display_name: z.string().trim().min(2, "Informe seu nome profissional."),
  professional_title: z.string().trim().max(120),
  council_type: z.string().trim().max(32),
  council_number: z.string().trim().max(40),
  council_region: z.string().trim().max(32),
  specialties_text: z.string().trim(),
  bio: z.string().trim().max(2000),
  public_email: z.string().trim().email("Informe um e-mail válido.").or(z.literal("")),
  professional_phone: z.string().trim().max(24),
  default_appointment_duration: z.coerce.number<number>().int().min(15).max(240),
  default_session_value: z.coerce.number<number>().min(0).max(999999),
  accepts_online: z.boolean(),
  accepts_in_person: z.boolean(),
  minimum_booking_notice_minutes: z.coerce.number<number>().int().min(0).max(43200),
  maximum_booking_days: z.coerce.number<number>().int().min(1).max(730),
  cancellation_notice_hours: z.coerce.number<number>().int().min(0).max(720),
  allow_online_booking: z.boolean(),
  allow_patient_portal: z.boolean(),
  send_appointment_reminders: z.boolean(),
  reminder_hours_before: z.coerce.number<number>().int().min(1).max(720),
  business_name_on_documents: z.string().trim().max(200),
  document_header: z.string().trim().max(2000),
  document_footer: z.string().trim().max(2000),
});

export type OrganizationOnboardingForm = z.infer<
  typeof organizationOnboardingSchema
>;
