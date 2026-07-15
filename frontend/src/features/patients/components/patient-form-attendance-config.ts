import type { PatientFieldConfig } from "./patient-form-personal-config";

export const ATTENDANCE_FIELD_CONFIG: PatientFieldConfig[] = [
  {
    name: "attendance_type",
    label: "Tipo de atendimento",
    type: "select",
    options: [
      ["individual", "Individual"],
      ["couple", "Casal"],
      ["family", "Familiar"],
      ["group", "Grupo"],
      ["other", "Outro"],
    ],
  },
  {
    name: "modality",
    label: "Modalidade",
    type: "select",
    options: [
      ["in_person", "Presencial"],
      ["online", "Online"],
      ["hybrid", "Híbrido"],
    ],
  },
  {
    name: "payer_type",
    label: "Tipo de pagador",
    type: "select",
    options: [
      ["private", "Particular"],
      ["insurance", "Convênio"],
    ],
  },
  { name: "session_value", label: "Valor do atendimento", mask: "money" },
  {
    name: "planned_frequency",
    label: "Frequência",
    type: "select",
    options: [
      ["", "Não definida"],
      ["weekly", "Semanal"],
      ["biweekly", "Quinzenal"],
      ["monthly", "Mensal"],
      ["as_needed", "Conforme necessidade"],
    ],
  },
  {
    name: "reminder_recipient",
    label: "Destinatário dos lembretes",
    type: "select",
    full: true,
    options: [
      ["patient", "Paciente"],
      ["financial_responsible", "Responsável financeiro"],
      ["both", "Ambos"],
      ["none", "Não enviar"],
    ],
  },
  { name: "tags", label: "Etiquetas", full: true },
  { name: "referral_source", label: "Origem / indicação", full: true },
];
