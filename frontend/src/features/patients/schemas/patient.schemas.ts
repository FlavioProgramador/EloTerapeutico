/**
 * Schemas de validação Zod para pacientes.
 */

import { z } from "zod";

const cpfRegex = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;
const phoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;

export const patientSchema = z.object({
  full_name: z
    .string()
    .min(1, "Nome completo é obrigatório.")
    .min(3, "O nome deve ter pelo menos 3 caracteres.")
    .max(150, "O nome não pode ter mais de 150 caracteres."),
  email: z
    .string()
    .email("Informe um e-mail válido.")
    .optional()
    .or(z.literal("")),
  phone: z
    .string()
    .regex(phoneRegex, "Formato: (99) 99999-9999.")
    .optional()
    .or(z.literal("")),
  birth_date: z.string().optional().or(z.literal("")),
  cpf: z
    .string()
    .regex(cpfRegex, "CPF inválido. Formato: 000.000.000-00.")
    .optional()
    .or(z.literal("")),
  gender: z.enum(["M", "F", "O", "N"]).optional(),
  address: z.string().optional().or(z.literal("")),
  status: z
    .enum(["active", "inactive", "on_hold"]),
  session_value: z
    .string()
    .optional()
    .or(z.literal("")),
  payment_method: z
    .enum(["pix", "credit_card", "cash", "insurance", "boleto"])
    .optional(),

  referral_source: z.string().max(255).optional().or(z.literal("")),
  guardian_name: z.string().max(255).optional().or(z.literal("")),
  guardian_cpf: z
    .string()
    .regex(cpfRegex, "CPF inválido. Formato: 000.000.000-00.")
    .optional()
    .or(z.literal("")),
  emergency_contact_name: z.string().max(150).optional().or(z.literal("")),
  emergency_contact_phone: z
    .string()
    .regex(phoneRegex, "Formato: (99) 99999-9999.")
    .optional()
    .or(z.literal("")),
  notes: z.string().max(2000, "Observações limitadas a 2000 caracteres.").optional().or(z.literal("")),
});

export type PatientFormData = z.infer<typeof patientSchema>;
