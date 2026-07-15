"use client";

import type { FieldPath, UseFormReturn } from "react-hook-form";

import { EMPTY_PATIENT_FORM } from "../components/patient-form-defaults";
import {
  toPatientMultipart,
  toPatientRequest,
} from "../components/patient-form-submit";
import type { PatientFormData } from "../schemas/patient.schemas";
import { useCreatePatient, useUpdatePatient } from "./use-patients";

interface Options {
  patientId?: number;
  form: UseFormReturn<PatientFormData>;
  onClose: () => void;
  onSaved: (patientId: number) => void;
  onError: (error: unknown) => void;
}

export function usePatientFormSubmit(options: Options) {
  const createMutation = useCreatePatient();
  const updateMutation = useUpdatePatient(options.patientId);
  const editing = Boolean(options.patientId);
  const pending = createMutation.isPending || updateMutation.isPending;

  const submit = options.form.handleSubmit(
    async (data) => {
      const request = toPatientRequest(data);
      const payload =
        data.photo instanceof File
          ? toPatientMultipart(request, data.photo)
          : request;
      try {
        const saved = editing
          ? await updateMutation.mutateAsync(payload)
          : await createMutation.mutateAsync(payload);
        options.form.reset(EMPTY_PATIENT_FORM);
        options.onSaved(saved.id);
        options.onClose();
      } catch (error) {
        options.onError(error);
      }
    },
    (invalid) => {
      const first = Object.keys(invalid)[0] as
        | FieldPath<PatientFormData>
        | undefined;
      if (first) options.form.setFocus(first);
    },
  );

  return { editing, pending, submit };
}
