import { z } from "zod";

export const organizationOnboardingSchema = z.object({
  name: z.string().trim().min(2, "Informe o nome do consultório ou clínica."),
  organization_type: z.enum(["individual", "clinic", "company"]),
  legal_name: z.string().trim().max(200).optional().default(""),
  document: z.string().trim().max(32).optional().default(""),
  email: z.string().trim().email("Informe um e-mail válido.").or(z.literal("")),
  phone: z.string().trim().max(24).optional().default(""),
  timezone: z.string().trim().min(1).default("America/Sao_Paulo"),
  display_name: z.string().trim().min(2, "Informe seu nome profissional."),
  professional_title: z.string().trim().max(120).optional().default(""),
  council_type: z.string().trim().max(32).optional().default(""),
  council_number: z.string().trim().max(40).optional().default(""),
  council_region: z.string().trim().max(32).optional().default(""),
  specialties_text: z.string().trim().optional().default(""),
  bio: z.string().trim().max(2000).optional().default(""),
  public_email: z.string().trim().email("Informe um e-mail válido.").or(z.literal("")),
  professional_phone: z.string().trim().max(24).optional().default(""),
  default_appointment_duration: z.coerce.number().int().min(15).max(240),
  default_session_value: z.coerce.number().min(0).max(999999),
  accepts_online: z.boolean(),
  accepts_in_person: z.boolean(),
  minimum_booking_notice_minutes: z.coerce.number().int().min(0).max(43200),
  maximum_booking_days: z.coerce.number().int().min(1).max(730),
  cancellation_notice_hours: z.coerce.number().int().min(0).max(720),
  allow_online_booking: z.boolean(),
  allow_patient_portal: z.boolean(),
  send_appointment_reminders: z.boolean(),
  reminder_hours_before: z.coerce.number().int().min(1).max(720),
  business_name_on_documents: z.string().trim().max(200).optional().default(""),
  document_header: z.string().trim().max(2000).optional().default(""),
  document_footer: z.string().trim().max(2000).optional().default(""),
});

export type OrganizationOnboardingForm = z.infer<
  typeof organizationOnboardingSchema
>;
