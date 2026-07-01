import { z } from "zod";

import {
  optionalCpf,
  optionalPhone,
  optionalText,
} from "./patient-schema-common";

export const patientContactFields = {
  address: optionalText,
  address_zip_code: optionalText,
  address_street: z.string().trim().max(255).optional().or(z.literal("")),
  address_number: z.string().trim().max(30).optional().or(z.literal("")),
  address_complement: z.string().trim().max(120).optional().or(z.literal("")),
  address_neighborhood: z.string().trim().max(120).optional().or(z.literal("")),
  address_city: z.string().trim().max(120).optional().or(z.literal("")),
  address_state: z
    .string()
    .regex(
      /^(|AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)$/,
      "Selecione uma UF válida.",
    ),
  emergency_contact_name: z.string().trim().max(255).optional().or(z.literal("")),
  emergency_contact_relationship: z.string().trim().max(80).optional().or(z.literal("")),
  emergency_contact_phone: optionalPhone,
  guardian_name: z.string().trim().max(255).optional().or(z.literal("")),
  guardian_cpf: optionalCpf,
  guardian_phone: optionalPhone,
  guardian_email: z.string().trim().email("Informe um e-mail válido.").optional().or(z.literal("")),
  guardian_relationship: z.string().trim().max(80).optional().or(z.literal("")),
};
