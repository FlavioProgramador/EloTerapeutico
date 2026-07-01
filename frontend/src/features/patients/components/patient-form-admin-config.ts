import type { PatientFieldConfig } from "./patient-form-personal-config";

export const DOCUMENT_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "cpf", label: "CPF *", mask: "cpf" },
  { name: "rg", label: "RG" },
  { name: "profession", label: "Profissão" },
  { name: "social_network", label: "Rede social" },
];

export const ADDRESS_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "address_zip_code", label: "CEP", mask: "cep" },
  { name: "address_street", label: "Rua / Avenida" },
  { name: "address_number", label: "Número" },
  { name: "address_complement", label: "Complemento" },
  { name: "address_neighborhood", label: "Bairro" },
  { name: "address_city", label: "Cidade" },
  { name: "address_state", label: "Estado" },
];

export const EMERGENCY_FIELD_CONFIG: PatientFieldConfig[] = [
  { name: "emergency_contact_name", label: "Nome do contato" },
  {
    name: "emergency_contact_phone",
    label: "Telefone de emergência",
    mask: "phone",
  },
  {
    name: "emergency_contact_relationship",
    label: "Vínculo",
    full: true,
  },
];
