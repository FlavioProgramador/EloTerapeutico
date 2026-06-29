import { z } from "zod";

const cpfRegex = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;
const phoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
const optionalPhone = z.string().regex(phoneRegex, "Formato: (99) 99999-9999.").optional().or(z.literal(""));
const optionalCpf = z.string().regex(cpfRegex, "Formato: 000.000.000-00.").optional().or(z.literal(""));

export const patientSchema = z
  .object({
    full_name: z.string().min(3, "Informe o nome completo.").max(255),
    social_name: z.string().max(255).optional().or(z.literal("")),
    email: z.string().email("Informe um e-mail válido.").optional().or(z.literal("")),
    phone: optionalPhone,
    whatsapp: optionalPhone,
    birth_date: z.string().min(1, "Data de nascimento é obrigatória."),
    cpf: z.string().regex(cpfRegex, "CPF inválido. Formato: 000.000.000-00."),
    rg: z.string().max(30).optional().or(z.literal("")),
    gender: z.enum(["M", "F", "O", "N"]),
    marital_status: z.string().optional().or(z.literal("")),
    address: z.string().optional().or(z.literal("")),
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
    insurance_name: z.string().max(120).optional().or(z.literal("")),
    session_value: z.string().optional().or(z.literal("")),
    planned_frequency: z.string().optional().or(z.literal("")),
    tags: z.string().optional().or(z.literal("")),
    referral_source: z.string().max(255).optional().or(z.literal("")),
    emergency_contact_name: z.string().max(255).optional().or(z.literal("")),
    emergency_contact_relationship: z.string().max(80).optional().or(z.literal("")),
    emergency_contact_phone: optionalPhone,
    guardian_name: z.string().max(255).optional().or(z.literal("")),
    guardian_cpf: optionalCpf,
    guardian_phone: optionalPhone,
    guardian_email: z.string().email("Informe um e-mail válido.").optional().or(z.literal("")),
    guardian_relationship: z.string().max(80).optional().or(z.literal("")),
    consent_terms_accepted: z.boolean(),
    notes: z.string().max(2000).optional().or(z.literal("")),
  })
  .superRefine((data, context) => {
    if (data.payer_type === "insurance" && !data.insurance_name) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["insurance_name"],
        message: "Informe o convênio.",
      });
    }

    const birth = new Date(`${data.birth_date}T12:00:00`);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const month = today.getMonth() - birth.getMonth();
    if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) age -= 1;
    if (age < 18 && !data.guardian_name) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["guardian_name"],
        message: "Informe o responsável legal.",
      });
    }
  });

export type PatientFormData = z.infer<typeof patientSchema>;
