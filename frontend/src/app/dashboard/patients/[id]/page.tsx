"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  CalendarDays,
  ClipboardList,
  Edit2,
  Mail,
  MapPin,
  Phone,
  Trash2,
  UserRound,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { Badge, getPatientStatusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Modal } from "@/components/ui/modal";
import {
  useDeletePatient,
  usePatient,
  useUpdatePatient,
} from "@/features/patients/hooks/use-patients";
import {
  patientSchema,
  type PatientFormData,
} from "@/features/patients/schemas/patient.schemas";
import type { CreatePatientPayload, PatientStatus } from "@/types";

const fieldClass =
  "h-10 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/15";

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

function normalizeStatus(status: PatientStatus): PatientFormData["status"] {
  return status === "on_hold" ? "waiting_return" : status;
}

function Detail({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium text-foreground">
        {value || "Não informado"}
      </p>
    </div>
  );
}

export default function PatientDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const patientId = Number(params.id);
  const [editOpen, setEditOpen] = useState(false);
  const patientQuery = usePatient(patientId);
  const updateMutation = useUpdatePatient(patientId);
  const deleteMutation = useDeletePatient();
  const patient = patientQuery.data;

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      full_name: "",
      social_name: "",
      cpf: "",
      rg: "",
      birth_date: "",
      gender: "N",
      marital_status: "",
      email: "",
      phone: "",
      whatsapp: "",
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
    if (!patient) return;
    const address =
      typeof patient.address === "string"
        ? patient.address
        : (patient.address as Record<string, string> | undefined)?.street || "";
    reset({
      full_name: patient.full_name || "",
      social_name: patient.social_name || "",
      cpf: patient.cpf ? formatCpf(patient.cpf) : "",
      rg: patient.rg || "",
      birth_date: patient.birth_date || "",
      gender: patient.gender || "N",
      marital_status: patient.marital_status || "",
      email: patient.email || "",
      phone: patient.phone || "",
      whatsapp: patient.whatsapp || "",
      address,
      status: normalizeStatus(patient.status),
      attendance_type:
        (patient.attendance_type as PatientFormData["attendance_type"]) ||
        "individual",
      modality:
        (patient.modality as PatientFormData["modality"]) || "in_person",
      payer_type:
        (patient.payer_type as PatientFormData["payer_type"]) || "private",
      insurance_name: patient.insurance_name || "",
      session_value: patient.session_value || "",
      planned_frequency: patient.planned_frequency || "",
      tags: (patient.tags ?? []).join(", "),
      referral_source: patient.referral_source || "",
      emergency_contact_name: patient.emergency_contact_name || "",
      emergency_contact_relationship:
        patient.emergency_contact_relationship || "",
      emergency_contact_phone: patient.emergency_contact_phone || "",
      guardian_name: patient.guardian_name || "",
      guardian_cpf: patient.guardian_cpf
        ? formatCpf(patient.guardian_cpf)
        : "",
      guardian_phone: patient.guardian_phone || "",
      guardian_email: patient.guardian_email || "",
      guardian_relationship: patient.guardian_relationship || "",
      consent_terms_accepted: patient.consent_terms_accepted || false,
      notes: patient.notes || "",
    });
  }, [patient, reset]);

  const birthDate = watch("birth_date");
  const payerType = watch("payer_type");
  const isMinor = useMemo(() => {
    if (!birthDate) return false;
    const birth = new Date(`${birthDate}T12:00:00`);
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const month = today.getMonth() - birth.getMonth();
    if (month < 0 || (month === 0 && today.getDate() < birth.getDate())) {
      age -= 1;
    }
    return age < 18;
  }, [birthDate]);

  const submit = handleSubmit(async (data) => {
    const { tags, address, ...values } = data;
    const optional = (value?: string) => value?.trim() || undefined;
    const payload: Partial<CreatePatientPayload> = {
      ...values,
      social_name: optional(values.social_name),
      rg: optional(values.rg),
      email: optional(values.email),
      phone: optional(values.phone),
      whatsapp: optional(values.whatsapp),
      address: address ? { street: address.trim() } : undefined,
      insurance_name: optional(values.insurance_name),
      session_value: optional(values.session_value) || "0.00",
      planned_frequency: optional(values.planned_frequency),
      tags: tags
        ? tags
            .split(",")
            .map((tag) => tag.trim())
            .filter(Boolean)
        : [],
      referral_source: optional(values.referral_source),
      emergency_contact_name: optional(values.emergency_contact_name),
      emergency_contact_relationship: optional(
        values.emergency_contact_relationship,
      ),
      emergency_contact_phone: optional(values.emergency_contact_phone),
      guardian_name: isMinor ? optional(values.guardian_name) : undefined,
      guardian_cpf: isMinor ? optional(values.guardian_cpf) : undefined,
      guardian_phone: isMinor ? optional(values.guardian_phone) : undefined,
      guardian_email: isMinor ? optional(values.guardian_email) : undefined,
      guardian_relationship: isMinor
        ? optional(values.guardian_relationship)
        : undefined,
      notes: optional(values.notes),
    };
    await updateMutation.mutateAsync(payload);
    setEditOpen(false);
    await patientQuery.refetch();
  });

  const archive = () => {
    if (!patient) return;
    if (!window.confirm(`Arquivar o cadastro de ${patient.full_name}?`)) return;
    deleteMutation.mutate(patient.id, {
      onSuccess: () => router.push("/dashboard/patients"),
    });
  };

  if (patientQuery.isLoading) {
    return <div className="h-[34rem] animate-pulse rounded-xl bg-secondary" />;
  }

  if (!patient) {
    return (
      <div className="rounded-xl border border-dashed border-border p-12 text-center">
        <h1 className="text-base font-bold text-foreground">
          Paciente não encontrado
        </h1>
        <Button className="mt-4" variant="outline" onClick={() => router.push("/dashboard/patients")}>
          Voltar para pacientes
        </Button>
      </div>
    );
  }

  const address =
    typeof patient.address === "string"
      ? patient.address
      : (patient.address as Record<string, string> | undefined)?.street;

  return (
    <div className="space-y-5">
      <button
        type="button"
        onClick={() => router.push("/dashboard/patients")}
        className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> Voltar para pacientes
      </button>

      <header className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <span className="grid h-12 w-12 place-items-center rounded-full border border-primary/25 bg-primary/10 text-lg font-bold text-primary">
            {patient.full_name.charAt(0).toUpperCase()}
          </span>
          <div>
            <h1 className="text-xl font-bold text-foreground">
              {patient.social_name || patient.full_name}
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant={getPatientStatusVariant(patient.status)}>
                {patient.status_display || patient.status}
              </Badge>
              <span className="text-[10px] text-muted-foreground">
                Cadastrado em {new Date(patient.created_at).toLocaleDateString("pt-BR")}
              </span>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={() => router.push(`/dashboard/records/${patient.id}`)}
            leftIcon={<ClipboardList className="h-4 w-4" />}
          >
            Ver prontuário
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setEditOpen(true)}
            leftIcon={<Edit2 className="h-4 w-4" />}
          >
            Editar cadastro
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={archive}
            isLoading={deleteMutation.isPending}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Arquivar
          </Button>
        </div>
      </header>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <UserRound className="h-4 w-4 text-primary" /> Dados cadastrais
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <Detail label="Nome completo" value={patient.full_name} />
            <Detail label="CPF" value={patient.formatted_cpf || patient.masked_cpf} />
            <Detail
              label="Nascimento"
              value={
                patient.birth_date
                  ? `${new Date(`${patient.birth_date}T12:00:00`).toLocaleDateString("pt-BR")} ${patient.age !== undefined ? `• ${patient.age} anos` : ""}`
                  : undefined
              }
            />
            <Detail label="Terapeuta" value={patient.therapist_name} />
            <Detail label="Modalidade" value={patient.modality} />
            <Detail label="Atendimento" value={patient.payer_type} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Contato</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="flex items-center gap-2 text-sm text-foreground">
              <Phone className="h-4 w-4 text-primary" />
              {patient.phone || "Não informado"}
            </p>
            <p className="flex items-center gap-2 text-sm text-foreground">
              <Mail className="h-4 w-4 text-primary" />
              {patient.email || "Não informado"}
            </p>
            <p className="flex items-start gap-2 text-sm text-foreground">
              <MapPin className="mt-0.5 h-4 w-4 text-primary" />
              {address || "Não informado"}
            </p>
          </CardContent>
        </Card>

        <Card className="xl:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CalendarDays className="h-4 w-4 text-primary" /> Informações de atendimento
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <Detail label="Tipo" value={patient.attendance_type} />
            <Detail label="Frequência" value={patient.planned_frequency} />
            <Detail label="Convênio" value={patient.insurance_name} />
            <Detail
              label="Valor da sessão"
              value={
                patient.session_value
                  ? Number(patient.session_value).toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })
                  : undefined
              }
            />
          </CardContent>
        </Card>
      </div>

      <Modal
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        title="Editar cadastro do paciente"
        description="Atualize os dados administrativos sem alterar o conteúdo clínico do prontuário."
        className="max-w-4xl"
      >
        <form onSubmit={submit} className="max-h-[72vh] space-y-4 overflow-y-auto pr-1">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
              Nome completo
              <input {...register("full_name")} className={fieldClass} />
              {errors.full_name && <span className="text-[10px] text-destructive">{errors.full_name.message}</span>}
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Nome social
              <input {...register("social_name")} className={fieldClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              CPF
              <input
                {...register("cpf")}
                onChange={(event) =>
                  setValue("cpf", formatCpf(event.target.value), {
                    shouldValidate: true,
                  })
                }
                className={fieldClass}
              />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Data de nascimento
              <input type="date" {...register("birth_date")} className={fieldClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Status
              <select {...register("status")} className={fieldClass}>
                <option value="active">Ativo</option>
                <option value="evaluation">Em avaliação</option>
                <option value="waiting_return">Aguardando retorno</option>
                <option value="discharged">Alta</option>
                <option value="inactive">Encerrado</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Telefone
              <input
                {...register("phone")}
                onChange={(event) =>
                  setValue("phone", formatPhone(event.target.value), {
                    shouldValidate: true,
                  })
                }
                className={fieldClass}
              />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              WhatsApp
              <input
                {...register("whatsapp")}
                onChange={(event) =>
                  setValue("whatsapp", formatPhone(event.target.value), {
                    shouldValidate: true,
                  })
                }
                className={fieldClass}
              />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              E-mail
              <input type="email" {...register("email")} className={fieldClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2 lg:col-span-3">
              Endereço
              <input {...register("address")} className={fieldClass} />
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Modalidade
              <select {...register("modality")} className={fieldClass}>
                <option value="in_person">Presencial</option>
                <option value="online">Online</option>
                <option value="hybrid">Híbrido</option>
              </select>
            </label>
            <label className="space-y-1 text-xs text-muted-foreground">
              Forma de atendimento
              <select {...register("payer_type")} className={fieldClass}>
                <option value="private">Particular</option>
                <option value="insurance">Convênio</option>
              </select>
            </label>
            {payerType === "insurance" && (
              <label className="space-y-1 text-xs text-muted-foreground">
                Convênio
                <input {...register("insurance_name")} className={fieldClass} />
              </label>
            )}
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2">
              Etiquetas, separadas por vírgula
              <input {...register("tags")} className={fieldClass} />
            </label>
            {isMinor && (
              <label className="space-y-1 text-xs text-muted-foreground">
                Responsável legal
                <input {...register("guardian_name")} className={fieldClass} />
              </label>
            )}
            <label className="space-y-1 text-xs text-muted-foreground sm:col-span-2 lg:col-span-3">
              Observações administrativas
              <textarea {...register("notes")} rows={4} className={`${fieldClass} h-auto py-3`} />
            </label>
          </div>
          <div className="flex justify-end gap-2 border-t border-border pt-4">
            <Button type="button" variant="ghost" onClick={() => setEditOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={updateMutation.isPending}>
              Salvar alterações
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
