import type { PatientFieldConfig } from "./patient-form-personal-config";

const MARITAL: Array<[string, string]> = [
  ["", "Não informado"],
  ["single", "Solteiro(a)"],
  ["married", "Casado(a)"],
  ["divorced", "Divorciado(a)"],
  ["widowed", "Viúvo(a)"],
  ["other", "Outro"],
];

export const FINANCIAL_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "financial_responsible_name", label: "Nome" },
  { name: "financial_responsible_cpf", label: "CPF", mask: "cpf" },
  { name: "financial_responsible_phone", label: "Telefone", mask: "phone" },
  {
    name: "financial_responsible_email",
    label: "E-mail",
    type: "email",
  },
  {
    name: "financial_responsible_marital_status",
    label: "Estado civil",
    type: "select",
    options: MARITAL,
  },
  { name: "financial_responsible_naturality", label: "Naturalidade" },
  { name: "financial_responsible_occupation", label: "Ocupação" },
  { name: "financial_responsible_relationship", label: "Relacionamento" },
];

export const GUARDIAN_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "guardian_name", label: "Nome" },
  { name: "guardian_cpf", label: "CPF", mask: "cpf" },
  { name: "guardian_phone", label: "Telefone", mask: "phone" },
  { name: "guardian_email", label: "E-mail", type: "email" },
  { name: "guardian_relationship", label: "Relacionamento", full: true },
];
