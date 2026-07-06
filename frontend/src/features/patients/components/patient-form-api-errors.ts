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
  let payload = error.response.data as Record<string, unknown>;
  
  // Unwrap backend custom exception handler envelope: {"error": {"details": {...}, "message": "..."}}
  if (payload.error && typeof payload.error === "object") {
    const errorObj = payload.error as Record<string, unknown>;
    if (errorObj.details && typeof errorObj.details === "object") {
      payload = errorObj.details as Record<string, unknown>;
    } else if (errorObj.message && typeof errorObj.message === "string") {
      toast.error(errorObj.message);
      return;
    }
  }
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
    } else if (key === "detail" || key === "non_field_errors") {
      toast.error(message);
    } else {
      // Show unmapped errors so they aren't swallowed silently
      toast.error(`Erro em ${key}: ${message}`);
    }
  });
  if (first) form.setFocus(first);
}
