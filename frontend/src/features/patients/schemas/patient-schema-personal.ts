import { z } from "zod";

import {
  isValidCpf,
  optionalPhone,
  optionalText,
} from "./patient-schema-common";

export const patientPersonalFields = {
  photo: z.custom<File | null>().optional().nullable(),
  remove_photo: z.boolean(),
  full_name: z.string().trim().min(3, "Informe o nome completo.").max(255),
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
  treatment_start_date: optionalText,
  cpf: z.string().refine(isValidCpf, "Informe um CPF válido."),
  rg: z.string().trim().max(30).optional().or(z.literal("")),
  profession: z.string().trim().max(160).optional().or(z.literal("")),
  social_network: z.string().trim().max(160).optional().or(z.literal("")),
  gender: z.enum(["M", "F", "O", "N"]),
  marital_status: optionalText,
};
