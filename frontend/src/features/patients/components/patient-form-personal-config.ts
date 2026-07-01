import type { PatientFormData } from "../schemas/patient.schemas";

export interface PatientFieldConfig {
  name: keyof PatientFormData;
  label: string;
  type?: "text" | "email" | "date" | "select";
  full?: boolean;
  mask?: "cpf" | "phone" | "cep" | "money";
  options?: Array<[string, string]>;
}

export const PERSONAL_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "full_name", label: "Nome completo *", full: true },
  { name: "social_name", label: "Nome social", full: true },
  { name: "email", label: "E-mail", type: "email" },
  { name: "phone", label: "Telefone", mask: "phone" },
  { name: "whatsapp", label: "WhatsApp", mask: "phone" },
  { name: "birth_date", label: "Data de nascimento *", type: "date" },
  { name: "treatment_start_date", label: "Início dos atendimentos", type: "date" },
];
