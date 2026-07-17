import type { BillingModel, BillingType } from "../types";

export const billingTypeLabels: Record<BillingType, string> = {
  PIX: "PIX",
  BOLETO: "Boleto",
  CREDIT_CARD: "Cartão de crédito",
};

export const billingModelLabels: Record<BillingModel, string> = {
  RECURRING: "Cobrança recorrente",
  ONE_TIME: "Pagamento anual à vista",
  INSTALLMENT: "Pagamento anual parcelado",
};

export const featureLabels: Record<string, string> = {
  agenda: "Agenda",
  patients: "Pacientes",
  clinical_records: "Prontuário",
  financial: "Financeiro",
  documents: "Documentos",
  forms: "Formulários",
  reports: "Relatórios",
  ai: "IA",
};
