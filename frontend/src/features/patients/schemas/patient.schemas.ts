import { z } from "zod";

const phoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
const ufRegex = /^(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)$/;

function isValidCpf(value: string) {
  const cpf = value.replace(/\D/g, "");
  if (cpf.length !== 11 || /^(\d)\1+$/.test(cpf)) return false;
  const calculate = (length: number) => {
    let sum = 0;
    for (let index = 0; index < length; index += 1) {
      sum += Number(cpf[index]) * (length + 1 - index);
    }
    const result = (sum * 10) % 11;
    return result === 10 ? 0 : result;
  };
  return calculate(9) === Number(cpf[9]) && calculate(10) === Number(cpf[10]);
}

const optional = z.string().optional().or(z.literal(""));
const optionalPhone = z
  .string()
  .regex(phoneRegex, "Formato: (99) 99999-9999.")
  .optional()
  .or(z.literal(""));
const optionalCpf = z
  .string()
  .refine((value) => !value || isValidCpf(value), "Informe um CPF válido.")
  .optional()
  .or(z.literal(""));

export const patientSchema = z
  .object({
    photo: z.custom<File | null>().optional().nullable(),
    remove_photo: z.boolean(),
    full_name: z
      .string()
      .trim()
      .min(3, "Informe o nome completo.")
      .max(255, "Utilize no máximo 255 caracteres."),
    social_name: z.string().trim().max(255).optional().or(z.literal("")),
    email: z
      .string()
      .trim()
      .email("Informe um e-mail válido.")
      .optional()
      .or(z.literal("")),
    phone: optionalPhone,
    whatsapp: optionalPhone,
    birth_date: z.string().min(1, "Informe a data de nascimento."),
    treatment_start_date: optional,
    cpf: z.string().refine(isValidCpf, "Informe um CPF válido."),
    rg: z.string().trim().max(30).optional().or(z.literal("")),
    profession: z.string().trim().max(160).optional().or(z.literal("")),
    social_network: z.string().trim().max(160).optional().or(z.literal("")),
    gender: z.enum(["M", "F", "O", "N"]),
    marital_status: optional,
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
    session_value: optional,
    planned_frequency: optional,
    reminders_enabled: z.boolean(),
    reminder_recipient: z.enum([
      "patient",
      "financial_responsible",
      "both",
      "none",
    ]),
    therapist: optional,
    tags: optional,
    referral_source: z.string().trim().max(255).optional().or(z.literal("")),
    address_zip_code: optional,
    address_street: z.string().trim().max(255).optional().or(z.literal("")),
    address_number: z.string().trim().max(30).optional().or(z.literal("")),
    address_complement: z.string().trim().max(120).optional().or(z.literal("")),
    address_neighborhood: z.string().trim().max(120).optional().or(z.literal("")),
    address_city: z.string().trim().max(120).optional().or(z.literal("")),
    address_state: z
      .string()
      .refine((value) => !value || ufRegex.test(value), "Selecione uma UF válida.")
      .optional()
      .or(z.literal("")),
    emergency_contact_name: z.string().trim().max(255).optional().or(z.literal("")),
    emergency_contact_relationship: z.string().trim().max(80).optional().or(z.literal("")),
    emergency_contact_phone: optionalPhone,
    guardian_name: z.string().trim().max(255).optional().or(z.literal("")),
    guardian_cpf: optionalCpf,
    guardian_phone: optionalPhone,
    guardian_email: z
      .string()
      .trim()
      .email("Informe um e-mail válido.")
      .optional()
      .or(z.literal("")),
    guardian_relationship: z.string().trim().max(80).optional().or(z.literal("")),
    financial_responsible_name: z.string().trim().max(255).optional().or(z.literal("")),
    financial_responsible_cpf: optionalCpf,
    financial_responsible_phone: optionalPhone,
    financial_responsible_email: z
      .string()
      .trim()
      .email("Informe um e-mail válido.")
      .optional()
      .or(z.literal("")),
    financial_responsible_marital_status: optional,
    financial_responsible_naturality: z.string().trim().max(120).optional().or(z.literal("")),
    financial_responsible_occupation: z.string().trim().max(160).optional().or(z.literal("")),
    financial_responsible_relationship: z.string().trim().max(80).optional().or(z.literal("")),
    consent_terms_accepted: z.boolean(),
    notes: z
      .string()
      .max(2000, "Utilize no máximo 2.000 caracteres.")
      .optional()
      .or(z.literal("")),
  })
  .superRefine((data, context) => {
    const today = new Date();
    const birth = new Date(`${data.birth_date}T12:00:00`);
    if (birth > today) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["birth_date"],
        message: "A data de nascimento não pode estar no futuro.",
      });
    }
    if (data.treatment_start_date) {
      const start = new Date(`${data.treatment_start_date}T12:00:00`);
      if (start > today) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["treatment_start_date"],
          message: "A data não pode estar no futuro.",
        });
      }
    }
    if (data.payer_type === "insurance" && !data.insurance_name) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["insurance_name"],
        message: "Informe o convênio.",
      });
    }
    if (data.session_value) {
      const normalized = Number(
        data.session_value.replace(/\./g, "").replace(",", "."),
      );
      if (!Number.isFinite(normalized) || normalized < 0) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["session_value"],
          message: "Informe um valor válido.",
        });
      }
    }
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
    if (["financial_responsible", "both"].includes(data.reminder_recipient)) {
      if (!data.financial_responsible_name) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["financial_responsible_name"],
          message: "Informe o responsável financeiro.",
        });
      }
      if (!data.financial_responsible_phone) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["financial_responsible_phone"],
          message: "Informe o telefone do responsável.",
        });
      }
    }
  });

export type PatientFormData = z.infer<typeof patientSchema>;
