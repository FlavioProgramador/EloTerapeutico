import type { RefinementCtx } from "zod";
import { z } from "zod";

interface PatientRuleData {
  birth_date: string;
  treatment_start_date?: string;
  payer_type: "private" | "insurance";
  insurance_name?: string;
  session_value?: string;
  guardian_name?: string;
  reminder_recipient: "patient" | "financial_responsible" | "both" | "none";
  financial_responsible_name?: string;
  financial_responsible_phone?: string;
}

function issue(context: RefinementCtx, path: string, message: string) {
  context.addIssue({ code: z.ZodIssueCode.custom, path: [path], message });
}

export function validatePatientRules(
  data: PatientRuleData,
  context: RefinementCtx,
) {
  const today = new Date();
  const birth = new Date(`${data.birth_date}T12:00:00`);
  if (birth > today) {
    issue(context, "birth_date", "A data de nascimento não pode estar no futuro.");
  }
  if (
    data.treatment_start_date &&
    new Date(`${data.treatment_start_date}T12:00:00`) > today
  ) {
    issue(context, "treatment_start_date", "A data não pode estar no futuro.");
  }
  if (data.payer_type === "insurance" && !data.insurance_name) {
    issue(context, "insurance_name", "Informe o convênio.");
  }
  if (data.session_value) {
    const value = Number(
      data.session_value.replace(/\./g, "").replace(",", "."),
    );
    if (!Number.isFinite(value) || value < 0) {
      issue(context, "session_value", "Informe um valor válido.");
    }
  }
  let age = today.getFullYear() - birth.getFullYear();
  const month = today.getMonth() - birth.getMonth();
  if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) age -= 1;
  if (age < 18 && !data.guardian_name) {
    issue(context, "guardian_name", "Informe o responsável legal.");
  }
  if (["financial_responsible", "both"].includes(data.reminder_recipient)) {
    if (!data.financial_responsible_name) {
      issue(context, "financial_responsible_name", "Informe o responsável financeiro.");
    }
    if (!data.financial_responsible_phone) {
      issue(context, "financial_responsible_phone", "Informe o telefone do responsável.");
    }
  }
}
