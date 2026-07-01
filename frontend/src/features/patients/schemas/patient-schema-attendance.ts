import { z } from "zod";

import { optionalText } from "./patient-schema-common";

export const patientAttendanceFields = {
  status: z.enum([
    "active",
    "evaluation",
    "waiting_return",
    "discharged",
    "inactive",
    "archived",
  ]),
  attendance_type: z.enum(["individual", "couple", "family", "group", "other"]),
  modality: z.enum(["in_person", "online", "hybrid"]),
  payer_type: z.enum(["private", "insurance"]),
  insurance_name: z.string().trim().max(120).optional().or(z.literal("")),
  session_value: optionalText,
  planned_frequency: optionalText,
  reminders_enabled: z.boolean(),
  reminder_recipient: z.enum([
    "patient",
    "financial_responsible",
    "both",
    "none",
  ]),
  therapist: optionalText,
  tags: optionalText,
  referral_source: z.string().trim().max(255).optional().or(z.literal("")),
};
