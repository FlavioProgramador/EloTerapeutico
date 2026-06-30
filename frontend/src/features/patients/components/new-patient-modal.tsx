"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import type { CreatePatientPayload } from "@/types";
import { useCreatePatient } from "../hooks/use-patients";
import {
  patientSchema,
  type PatientFormData,
} from "../schemas/patient.schemas";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated?: (patientId: number) => void;
}

const inputClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15";
const textareaClass = `${inputClass} h-auto min-h-24 py-3`;

function formatCpf(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  return digits
    .replace(/^(\d{3})(\d)/, "$1.$2")
    .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
    .replace(/\.(\d{3})(\d)/, ".$1-$2");
}

function formatPhone(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}

function FieldError({ message }: { message?: string }) {
  return message ? (
    <span className="text-[10px] text-destructive" role="alert">
      {message}
    </span>
  ) : null;
}

export function NewPatientModal({ open, onClose, onCreated }: Props) {
  const mutation = useCreatePatient();
  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      full_name: "",
      social_name: "",
      email: "",
      phone: "",
      whatsapp: "",
      birth_date: "",
      cpf: "",
      rg: "",
      gender: "N",
      marital_status: "",
      address: "",
      status: "active",
      attendance_type: "individual",
      modality: "in_person",
      payer_type: "private",
      insurance_name: "",
      session_value: "",
      planned_frequency: "",
      tags: "",
      referral_source: "",
      emergency_contact_name: "",
      emergency_contact_relationship: "",
      emergency_contact_phone: "",
      guardian_name: "",
      guardian_cpf: "",
      guardian_phone: "",
      guardian_email: "",
      guardian_relationship: "",
      consent_terms_accepted: false,
      notes: "",
    },
  });

  useEffect(() => {
    if (!open) reset();
  }, [open, reset]);

  const birthDate = watch("birth_date");
  const payerType = watch("payer_type");
  const isMinor = useMemo(() => {
    if (!birthDate) return false;
    const birth = new Date(`${birthDate}T12:00:00`);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const month = today.getMonth() - birth.getMonth();
    if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) age -= 1;
    return age < 18;
  }, [birthDate]);

  const submit = handleSubmit(async (data) => {
    const optional = (value?: string) => value?.trim() || undefined;
    const payload: CreatePatientPayload = {
      full_name: data.full_name.trim(),
      social_name: optional(data.social_name),
      cpf: data.cpf,
      rg: optional(data.rg),
      birth_date: data.birth_date,
      gender: data.gender,
      marital_status: optional(data.marital_status),
      email: optional(data.email),
      phone: optional(data.phone),
      whatsapp: optional(data.whatsapp),
      address: data.address ? { street: data.address.trim() } : undefined,
      status: data.status,
      attendance_type: data.attendance_type,
      modality: data.modality,
      payer_type: data.payer_type,
      insurance_name: optional(data.insurance_name),
      session_value: optional(data.session_value) || "0.00",
      planned_frequency: optional(data.planned_frequency),
      tags: data.tags
        ? data.tags.split(",").map((tag) => tag.trim()).filter(Boolean)
        : [],
      referral_source: optional(data.referral_source),
      emergency_contact_name: optional(data.emergency_contact_name),
      emergency_contact_relationship: optional(data.emergency_contact_relationship),
      emergency_contact_phone: optional(data.emergency_contact_phone),
      guardian_name: isMinor ? optional(data.guardian_name) : undefined,
      guardian_cpf: isMinor ? optional(data.guardian_cpf) : undefined,
      guardian_phone: isMinor ? optional(data.guardian_phone) : undefined,
      guardian_email: isMinor ? optional(data.guardian_email) : undefined,
      guardian_relationship: isMinor ? optional(data.guardian_relationship) : undefined,
      consent_terms_accepted: data.consent_terms_accepted,
      notes: optional(data.notes),
    };
    const patient = await mutation.mutateAsync(payload);
    reset();
    onClose();
    onCreated?.(patient.id);
  });

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="Cadastrar novo paciente"
      description="Organize o cadastro por seções. Dados clínicos devem ser registrados no prontuário."
      className="max-w-4xl"
    >
      <form onSubmit={submit} className="max-h-[72vh] space-y-4 overflow-y-auto pr-1" noValidate>
        <details open className="rounded-xl border border-border p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">Dados pessoais</summary>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
              Nome completo
              <input {...register("full_name")} className={inputClass} />
              <FieldError message={errors.full_name?.message} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Nome social
              <input {...register("social_name")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              CPF
              <input {...register("cpf")} onChange={(event) => setValue("cpf", formatCpf(event.target.value), { shouldValidate: true })} className={inputClass} placeholder="000.000.000-00" />
              <FieldError message={errors.cpf?.message} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              RG
              <input {...register("rg")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Data de nascimento
              <input type="date" {...register("birth_date")} className={inputClass} />
              <FieldError message={errors.birth_date?.message} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Gênero
              <select {...register("gender")} className={inputClass}>
                <option value="N">Prefiro não informar</option>
                <option value="F">Feminino</option>
                <option value="M">Masculino</option>
                <option value="O">Outro</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Estado civil
              <select {...register("marital_status")} className={inputClass}>
                <option value="">Não informado</option>
                <option value="single">Solteiro(a)</option>
                <option value="married">Casado(a)</option>
                <option value="divorced">Divorciado(a)</option>
                <option value="widowed">Viúvo(a)</option>
                <option value="other">Outro</option>
              </select>
            </label>
          </div>
        </details>

        <details open className="rounded-xl border border-border p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">Contato e atendimento</summary>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <label className="space-y-1 text-xs text-muted-foreground">Telefone
              <input {...register("phone")} onChange={(event) => setValue("phone", formatPhone(event.target.value), { shouldValidate: true })} className={inputClass} />
              <FieldError message={errors.phone?.message} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">WhatsApp
              <input {...register("whatsapp")} onChange={(event) => setValue("whatsapp", formatPhone(event.target.value), { shouldValidate: true })} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">E-mail
              <input type="email" {...register("email")} className={inputClass} />
              <FieldError message={errors.email?.message} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2 lg:col-span-3">Endereço
              <input {...register("address")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Status inicial
              <select {...register("status")} className={inputClass}>
                <option value="active">Ativo</option>
                <option value="evaluation">Em avaliação</option>
                <option value="waiting_return">Aguardando retorno</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Tipo de atendimento
              <select {...register("attendance_type")} className={inputClass}>
                <option value="individual">Individual</option>
                <option value="couple">Casal</option>
                <option value="family">Familiar</option>
                <option value="group">Grupo</option>
                <option value="other">Outro</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Modalidade
              <select {...register("modality")} className={inputClass}>
                <option value="in_person">Presencial</option>
                <option value="online">Online</option>
                <option value="hybrid">Híbrido</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Forma de atendimento
              <select {...register("payer_type")} className={inputClass}>
                <option value="private">Particular</option>
                <option value="insurance">Convênio</option>
              </select>
            </label>
            {payerType === "insurance" && (
              <label className="space-y-1 text-xs text-muted-foreground">Convênio
                <input {...register("insurance_name")} className={inputClass} />
                <FieldError message={errors.insurance_name?.message} />
              </label>
            )}
            <label className="space-y-1 text-xs text-muted-foreground">Valor da sessão
              <input type="number" min="0" step="0.01" {...register("session_value")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Frequência planejada
              <select {...register("planned_frequency")} className={inputClass}>
                <option value="">Não definida</option>
                <option value="weekly">Semanal</option>
                <option value="biweekly">Quinzenal</option>
                <option value="monthly">Mensal</option>
                <option value="as_needed">Conforme necessidade</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">Etiquetas, separadas por vírgula
              <input {...register("tags")} className={inputClass} placeholder="Ansiedade, particular, online" />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">Origem do paciente
              <input {...register("referral_source")} className={inputClass} />
            </label>
          </div>
        </details>

        <details className="rounded-xl border border-border p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">Contatos de segurança</summary>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <label className="space-y-1 text-xs text-muted-foreground">Contato de emergência
              <input {...register("emergency_contact_name")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Parentesco
              <input {...register("emergency_contact_relationship")} className={inputClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">Telefone
              <input {...register("emergency_contact_phone")} onChange={(event) => setValue("emergency_contact_phone", formatPhone(event.target.value), { shouldValidate: true })} className={inputClass} />
            </label>
          </div>
          {isMinor && (
            <div className="mt-4 grid gap-3 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-3">
              <label className="space-y-1 text-xs text-muted-foreground">Responsável legal
                <input {...register("guardian_name")} className={inputClass} />
                <FieldError message={errors.guardian_name?.message} />
              </label>
              <label className="space-y-1 text-xs text-muted-foreground">CPF do responsável
                <input {...register("guardian_cpf")} onChange={(event) => setValue("guardian_cpf", formatCpf(event.target.value), { shouldValidate: true })} className={inputClass} />
              </label>
              <label className="space-y-1 text-xs text-muted-foreground">Parentesco
                <input {...register("guardian_relationship")} className={inputClass} />
              </label>
              <label className="space-y-1 text-xs text-muted-foreground">Telefone
                <input {...register("guardian_phone")} onChange={(event) => setValue("guardian_phone", formatPhone(event.target.value), { shouldValidate: true })} className={inputClass} />
              </label>
              <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">E-mail
                <input type="email" {...register("guardian_email")} className={inputClass} />
              </label>
            </div>
          )}
        </details>

        <details className="rounded-xl border border-border p-4">
          <summary className="cursor-pointer text-sm font-semibold text-foreground">Informações complementares</summary>
          <div className="mt-4 space-y-3">
            <label className="space-y-1 text-xs text-muted-foreground">Observações administrativas
              <textarea {...register("notes")} className={textareaClass} />
            </label>
            <label className="flex items-start gap-2 text-xs text-muted-foreground">
              <input type="checkbox" {...register("consent_terms_accepted")} className="mt-0.5 accent-primary" />
              Confirmo que os consentimentos necessários foram coletados e registrados.
            </label>
          </div>
        </details>

        <div className="sticky bottom-0 flex justify-end gap-2 border-t border-border bg-card py-3">
          <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
          <Button type="submit" isLoading={mutation.isPending}>Cadastrar paciente</Button>
        </div>
      </form>
    </Modal>
  );
}
