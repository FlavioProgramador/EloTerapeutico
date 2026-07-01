import axios from "axios";
import type { FieldPath, UseFormReturn } from "react-hook-form";
import { toast } from "sonner";

import type { PatientFormData } from "../schemas/patient.schemas";
import { EMPTY_PATIENT_FORM } from "./patient-form-defaults";

export function applyPatientFormApiErrors(
  error: unknown,
  form: UseFormReturn<PatientFormData>,
) {
  if (!axios.isAxiosError(error) || !error.response?.data) {
    toast.error("Não foi possível salvar. Verifique sua conexão.");
    return;
  }
  const payload = error.response.data as Record<string, unknown>;
  let first: FieldPath<PatientFormData> | undefined;
  Object.entries(payload).forEach(([key, value]) => {
    const message = Array.isArray(value)
      ? value.map(String).join(" ")
      : typeof value === "string"
        ? value
        : undefined;
    if (!message) return;
    if (key in EMPTY_PATIENT_FORM) {
      const name = key as FieldPath<PatientFormData>;
      form.setError(name, { type: "server", message });
      first ??= name;
    } else if (key === "detail") {
      toast.error(message);
    }
  });
  if (first) form.setFocus(first);
}
