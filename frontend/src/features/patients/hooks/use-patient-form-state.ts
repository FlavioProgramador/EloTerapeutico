"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import type { ChangeEvent } from "react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "@/contexts/auth";
import { EMPTY_PATIENT_FORM } from "../components/patient-form-defaults";
import { recordToPatientForm } from "../components/patient-form-hydration";
import {
  patientSchema,
  type PatientFormData,
} from "../schemas/patient.schemas";
import { usePatient, usePatientProfessionals } from "./use-patients";

export function usePatientFormState(
  open: boolean,
  patientId: number | undefined,
  pending: boolean,
  onClose: () => void,
) {
  const { user } = useAuth();
  const patientQuery = usePatient(open ? patientId : undefined);
  const professionalsQuery = usePatientProfessionals();
  const [preview, setPreview] = useState<string | null>(null);
  const form = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: EMPTY_PATIENT_FORM,
  });
  const birthDate = form.watch("birth_date");

  const isMinor = useMemo(() => {
    if (!birthDate) return false;
    const birth = new Date(`${birthDate}T12:00:00`);
    const now = new Date();
    let age = now.getFullYear() - birth.getFullYear();
    if (
      now.getMonth() < birth.getMonth() ||
      (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())
    ) {
      age -= 1;
    }
    return age < 18;
  }, [birthDate]);

  useEffect(() => {
    if (!open) return;
    if (patientId && patientQuery.data) {
      form.reset(recordToPatientForm(patientQuery.data));
    } else if (!patientId) {
      form.reset({
        ...EMPTY_PATIENT_FORM,
        therapist: user?.role === "therapist" ? String(user.id) : "",
      });
    }
  }, [form, open, patientId, patientQuery.data, user]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const close = () => {
    if (pending) return;
    if (
      form.formState.isDirty &&
      !window.confirm("Há alterações não salvas. Deseja fechar mesmo assim?")
    ) {
      return;
    }
    form.reset(EMPTY_PATIENT_FORM);
    setPreview(null);
    onClose();
  };

  const changePhoto = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (
      !["image/jpeg", "image/png"].includes(file.type) ||
      file.size > 2 * 1024 * 1024
    ) {
      form.setError("photo", {
        message: "Envie uma imagem JPG ou PNG de até 2 MB.",
      });
      return;
    }
    if (preview) URL.revokeObjectURL(preview);
    setPreview(URL.createObjectURL(file));
    form.setValue("photo", file, {
      shouldDirty: true,
      shouldValidate: true,
    });
    form.setValue("remove_photo", false, { shouldDirty: true });
  };

  const removePhoto = () => {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    form.setValue("photo", null, { shouldDirty: true });
    form.setValue("remove_photo", true, { shouldDirty: true });
  };

  return {
    form,
    user,
    patientQuery,
    professionalsQuery,
    preview,
    isMinor,
    close,
    changePhoto,
    removePhoto,
  };
}
