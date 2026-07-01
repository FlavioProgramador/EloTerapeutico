import { z } from "zod";

import { optionalCpf, optionalPhone, optionalText } from "./patient-schema-common";

export const patientFinancialFields = {
  financial_responsible_name: z.string().trim().max(255).optional().or(z.literal("")),
  financial_responsible_cpf: optionalCpf,
  financial_responsible_phone: optionalPhone,
  financial_responsible_email: z.string().trim().email("Informe um e-mail válido.").optional().or(z.literal("")),
  financial_responsible_marital_status: optionalText,
  financial_responsible_naturality: optionalText,
  financial_responsible_occupation: optionalText,
  financial_responsible_relationship: optionalText,
  consent_terms_accepted: z.boolean(),
  notes: z.string().max(2000).optional().or(z.literal("")),
};
