"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  ArrowLeft,
  Calendar,
  ClipboardList,
  Edit2,
  Trash2,
  Phone,
  Mail,
  MapPin,
  CalendarDays,
  User,
  Heart,
  ShieldAlert,
  Info,
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";

import { usePatient, useUpdatePatient, useDeletePatient } from "@/features/patients/hooks/use-patients";
import { patientSchema, type PatientFormData } from "@/features/patients/schemas/patient.schemas";

// Funções utilitárias para formatação automática de inputs
const formatCPF = (value: string) => {
  const clean = value.replace(/\D/g, "").slice(0, 11);
  if (clean.length <= 3) return clean;
  if (clean.length <= 6) return `${clean.slice(0, 3)}.${clean.slice(3)}`;
  if (clean.length <= 9) return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6)}`;
  return `${clean.slice(0, 3)}.${clean.slice(3, 6)}.${clean.slice(6, 9)}-${clean.slice(9)}`;
};

const formatPhone = (value: string) => {
  const clean = value.replace(/\D/g, "").slice(0, 11);
  if (clean.length <= 2) return clean;
  if (clean.length <= 6) return `(${clean.slice(0, 2)}) ${clean.slice(2)}`;
  if (clean.length <= 10) return `(${clean.slice(0, 2)}) ${clean.slice(2, 6)}-${clean.slice(6)}`;
  return `(${clean.slice(0, 2)}) ${clean.slice(2, 7)}-${clean.slice(7)}`;
};

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // TanStack Query hooks
  const { data: patient, isLoading, refetch } = usePatient(patientId);
  const updatePatientMutation = useUpdatePatient(patientId);
  const deletePatientMutation = useDeletePatient();

  // Form com React Hook Form + Zod
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      full_name: "",
      cpf: "",
      birth_date: "",
      gender: "M",
      email: "",
      phone: "",
      address: "",
      status: "active",
      referral_source: "",
      guardian_name: "",
      guardian_cpf: "",
      notes: "",
    },
    mode: "onBlur",
  });

  // Preenche os dados do formulário quando o paciente é carregado
  useEffect(() => {
    if (patient) {
      reset({
        full_name: patient.full_name || "",
        cpf: patient.cpf || "",
        birth_date: patient.birth_date || "",
        gender: patient.gender || "M",
        email: patient.email || "",
        phone: patient.phone || "",
        address: typeof patient.address === "string" ? patient.address : (patient.address as any)?.street || "",
        status: patient.status || "active",
        referral_source: patient.referral_source || "",
        guardian_name: patient.guardian_name || "",
        guardian_cpf: patient.guardian_cpf || "",
        notes: patient.notes || "",
      });
    }
  }, [patient, reset]);

  // Monitora nascimento para calcular se é menor
  const birthDateValue = watch("birth_date");
  const [isMinor, setIsMinor] = useState(false);

  useEffect(() => {
    if (!birthDateValue) {
      setIsMinor(false);
      return;
    }
    try {
      const birth = new Date(birthDateValue);
      const today = new Date();
      let age = today.getFullYear() - birth.getFullYear();
      const m = today.getMonth() - birth.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
        age--;
      }
      setIsMinor(age < 18);
    } catch (e) {
      setIsMinor(false);
    }
  }, [birthDateValue]);

  // Função para salvar alterações (Edição)
  const onSubmit = async (data: PatientFormData) => {
    const payload = {
      ...data,
      email: data.email || undefined,
      phone: data.phone || undefined,
      birth_date: data.birth_date || undefined,
      cpf: data.cpf || undefined,
      guardian_name: isMinor ? data.guardian_name : undefined,
      guardian_cpf: isMinor ? data.guardian_cpf : undefined,
      notes: data.notes || undefined,
      address: data.address ? { street: data.address } : undefined, // Formato JSON esperado
    };

    updatePatientMutation.mutate(payload, {
      onSuccess: () => {
        setIsEditModalOpen(false);
        refetch();
      },
    });
  };

  // Função para arquivar (deletar) paciente
  const handleArchive = async () => {
    if (!confirm(`Deseja realmente arquivar o cadastro do paciente "${patient?.full_name}"?`)) return;
    deletePatientMutation.mutate(patientId, {
      onSuccess: () => {
        router.push("/dashboard/patients");
      },
    });
  };

  const getGenderLabel = (g?: string) => {
    if (!g) return "Não informado";
    const genders: Record<string, string> = {
      M: "Masculino",
      F: "Feminino",
      O: "Outro",
      N: "Prefiro não informar",
    };
    return genders[g] || g;
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-3">
        <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-muted-foreground animate-pulse">Carregando ficha...</span>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-4">
        <ShieldAlert className="h-10 w-10 text-destructive" />
        <div>
          <h3 className="font-bold text-sm text-foreground">Paciente não encontrado</h3>
          <p className="text-xs text-muted-foreground mt-1">
            O registro solicitado não existe ou foi removido do sistema.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push("/dashboard/patients")}>
          Voltar para CRM
        </Button>
      </div>
    );
  }

  const patientAddressString = typeof patient.address === "string"
    ? patient.address
    : (patient.address as any)?.street || "";

  return (
    <div className="space-y-6">
      {/* Botão Voltar */}
      <button
        onClick={() => router.push("/dashboard/patients")}
        className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <ArrowLeft className="h-4 w-4" />
        Voltar para lista de pacientes
      </button>

      {/* Header Ficha */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border/40 pb-6">
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-lg uppercase shrink-0">
            {patient.full_name.charAt(0)}
          </div>
          <div className="space-y-0.5">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {patient.full_name}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span>Cadastrado em {new Date(patient.created_at).toLocaleDateString("pt-BR")}</span>
              <span>•</span>
              <Badge variant={patient.status === "active" ? "success" : "muted"}>
                {patient.status === "active" ? "Em Tratamento" : "Alta/Inativo"}
              </Badge>
            </div>
          </div>
        </div>

        {/* Ações */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            onClick={() => router.push(`/dashboard/records/${patient.id}`)}
            leftIcon={<ClipboardList className="h-4 w-4" />}
            className="text-white font-semibold"
          >
            Ver Prontuário
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-border hover:bg-secondary/60 text-foreground"
            onClick={() => setIsEditModalOpen(true)}
            leftIcon={<Edit2 className="h-4 w-4" />}
          >
            Editar Cadastro
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-destructive/20 text-destructive hover:bg-destructive/5 cursor-pointer"
            onClick={handleArchive}
            leftIcon={<Trash2 className="h-4 w-4" />}
          >
            Arquivar
          </Button>
        </div>
      </div>

      {/* Grid Dados */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ficha Geral */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Info className="h-4.5 w-4.5 text-primary" />
                Dados Cadastrais
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 mt-1.5">
              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Nome Completo</p>
                <p className="text-sm font-semibold text-foreground">{patient.full_name}</p>
              </div>

              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">CPF</p>
                <p className="text-sm font-semibold text-foreground">{patient.formatted_cpf || "---"}</p>
              </div>

              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Data de Nascimento</p>
                <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <CalendarDays className="h-4 w-4 text-muted-foreground" />
                  <span>
                    {patient.birth_date ? new Date(patient.birth_date).toLocaleDateString("pt-BR") : "---"}
                    {patient.age !== undefined ? ` (${patient.age} anos)` : ""}
                  </span>
                </p>
              </div>

              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Gênero</p>
                <p className="text-sm font-semibold text-foreground">{getGenderLabel(patient.gender)}</p>
              </div>

              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Indicação / Origem</p>
                <p className="text-sm font-semibold text-foreground">{patient.referral_source || "Nenhuma informada"}</p>
              </div>

              <div className="space-y-0.5">
                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Terapeuta Responsável</p>
                <p className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>{patient.therapist_name || "---"}</span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Notas Clínicas de Entrada */}
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Heart className="h-4.5 w-4.5 text-primary" />
                Notas de Entrada / Queixa Principal
              </CardTitle>
            </CardHeader>
            <CardContent className="p-5 mt-1.5">
              {patient.notes ? (
                <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                  {patient.notes}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground italic">
                  Nenhuma anotação ou queixa inicial informada no cadastro.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Lateral: Contato & Responsável Legal */}
        <div className="space-y-6">
          {/* Informações de Contato */}
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-sm font-bold text-foreground">Informações de Contato</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3.5 mt-1.5">
              <div className="flex items-start gap-3">
                <Phone className="h-4.5 w-4.5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">WhatsApp / Telefone</p>
                  <a href={`tel:${patient.phone}`} className="text-xs font-semibold hover:underline text-foreground">
                    {patient.phone || "---"}
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Mail className="h-4.5 w-4.5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">E-mail</p>
                  {patient.email ? (
                    <a href={`mailto:${patient.email}`} className="text-xs font-semibold hover:underline text-foreground truncate max-w-[180px] block">
                      {patient.email}
                    </a>
                  ) : (
                    <span className="text-xs text-muted-foreground">Não cadastrado</span>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="h-4.5 w-4.5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Endereço Residencial</p>
                  <p className="text-xs text-foreground leading-relaxed">
                    {patientAddressString || "Não informado"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Responsável Legal (Condicional) */}
          {patient.age !== undefined && patient.age < 18 ? (
            <Card className="border-primary/20 bg-primary/5 shadow-xs relative overflow-hidden">
              <div className="absolute top-0 left-0 h-full w-[3px] bg-primary" />
              <CardHeader className="pb-3 border-b border-primary/10">
                <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                  <ShieldAlert className="h-4 w-4 text-primary shrink-0" />
                  Responsável Legal
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3 mt-1.5">
                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">Nome do Tutor</p>
                  <p className="text-xs font-semibold text-foreground">{patient.guardian_name || "---"}</p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase">CPF do Tutor</p>
                  <p className="text-xs font-semibold text-foreground">{patient.guardian_cpf || "---"}</p>
                </div>
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>

      {/* Modal de Edição */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Editar Cadastro do Paciente"
        description="Atualize as informações cadastrais e clique em salvar."
        className="max-w-xl"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1">
            <Input
              id="edit-patient-fullname"
              label="Nome Completo"
              placeholder="Nome completo do paciente"
              aria-invalid={!!errors.full_name}
              aria-describedby={errors.full_name ? "edit-patient-fullname-error" : undefined}
              error={errors.full_name?.message}
              {...register("full_name")}
            />
            {errors.full_name && (
              <p id="edit-patient-fullname-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.full_name.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="edit-patient-cpf"
                label="CPF"
                placeholder="000.000.000-00"
                aria-invalid={!!errors.cpf}
                aria-describedby={errors.cpf ? "edit-patient-cpf-error" : undefined}
                error={errors.cpf?.message}
                {...register("cpf", {
                  onChange: (e) => {
                    e.target.value = formatCPF(e.target.value);
                  }
                })}
              />
              {errors.cpf && (
                <p id="edit-patient-cpf-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.cpf.message}
                </p>
              )}
            </div>

            <div className="space-y-1">
              <Input
                id="edit-patient-birthdate"
                label="Data de Nascimento"
                type="date"
                aria-invalid={!!errors.birth_date}
                aria-describedby={errors.birth_date ? "edit-patient-birthdate-error" : undefined}
                error={errors.birth_date?.message}
                {...register("birth_date")}
              />
              {errors.birth_date && (
                <p id="edit-patient-birthdate-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.birth_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="edit-patient-gender" className="text-xs font-semibold text-muted-foreground">Gênero</label>
              <select
                id="edit-patient-gender"
                {...register("gender")}
                className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
                <option value="N">Prefiro não informar</option>
              </select>
            </div>

            <div className="space-y-1">
              <Input
                id="edit-patient-phone"
                label="Telefone / WhatsApp"
                placeholder="(11) 99999-9999"
                aria-invalid={!!errors.phone}
                aria-describedby={errors.phone ? "edit-patient-phone-error" : undefined}
                error={errors.phone?.message}
                {...register("phone", {
                  onChange: (e) => {
                    e.target.value = formatPhone(e.target.value);
                  }
                })}
              />
              {errors.phone && (
                <p id="edit-patient-phone-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.phone.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-1">
            <Input
              id="edit-patient-email"
              label="E-mail"
              placeholder="paciente@email.com"
              type="email"
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "edit-patient-email-error" : undefined}
              error={errors.email?.message}
              {...register("email")}
            />
            {errors.email && (
              <p id="edit-patient-email-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <Input
              id="edit-patient-address"
              label="Endereço Residencial"
              placeholder="Rua, Número, Bairro, Cidade..."
              aria-invalid={!!errors.address}
              aria-describedby={errors.address ? "edit-patient-address-error" : undefined}
              error={errors.address?.message}
              {...register("address")}
            />
            {errors.address && (
              <p id="edit-patient-address-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.address.message}
              </p>
            )}
          </div>

          {/* Responsável se Menor */}
          {isMinor && (
            <div className="p-4 rounded-md border border-primary/20 bg-primary/5 space-y-4 animate-scale-in">
              <div className="flex items-center gap-2 text-primary font-semibold text-xs">
                <ShieldAlert className="h-4 w-4" />
                <span>Paciente Menor de Idade (Requer Responsável)</span>
              </div>

              <div className="space-y-1">
                <Input
                  id="edit-patient-guardianname"
                  label="Nome do Responsável Legal"
                  placeholder="Nome completo do pai, mãe ou tutor"
                  aria-invalid={!!errors.guardian_name}
                  aria-describedby={errors.guardian_name ? "edit-patient-guardianname-error" : undefined}
                  error={errors.guardian_name?.message}
                  {...register("guardian_name")}
                  className="bg-card"
                />
                {errors.guardian_name && (
                  <p id="edit-patient-guardianname-error" className="text-xs text-destructive animate-fade-in" role="alert">
                    {errors.guardian_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <Input
                  id="edit-patient-guardiancpf"
                  label="CPF do Responsável Legal"
                  placeholder="000.000.000-00"
                  aria-invalid={!!errors.guardian_cpf}
                  aria-describedby={errors.guardian_cpf ? "edit-patient-guardiancpf-error" : undefined}
                  error={errors.guardian_cpf?.message}
                  {...register("guardian_cpf", {
                    onChange: (e) => {
                      e.target.value = formatCPF(e.target.value);
                    }
                  })}
                  className="bg-card"
                />
                {errors.guardian_cpf && (
                  <p id="edit-patient-guardiancpf-error" className="text-xs text-destructive animate-fade-in" role="alert">
                    {errors.guardian_cpf.message}
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="edit-patient-referral"
                label="Indicação / Origem"
                placeholder="Ex: Instagram, Google, Indicação"
                aria-invalid={!!errors.referral_source}
                aria-describedby={errors.referral_source ? "edit-patient-referral-error" : undefined}
                error={errors.referral_source?.message}
                {...register("referral_source")}
              />
              {errors.referral_source && (
                <p id="edit-patient-referral-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.referral_source.message}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="edit-patient-status" className="text-xs font-semibold text-muted-foreground">Status do Tratamento</label>
              <select
                id="edit-patient-status"
                {...register("status")}
                className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="active">Ativo (Em Tratamento)</option>
                <option value="inactive">Inativo (Alta/Pausa)</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <Textarea
              id="edit-patient-notes"
              label="Observações / Anotações Iniciais"
              placeholder="Histórico rápido, queixas clínicas..."
              aria-invalid={!!errors.notes}
              aria-describedby={errors.notes ? "edit-patient-notes-error" : undefined}
              error={errors.notes?.message}
              {...register("notes")}
            />
            {errors.notes && (
              <p id="edit-patient-notes-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.notes.message}
              </p>
            )}
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
              className="px-4"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              className="px-4 text-white font-semibold"
            >
              Salvar Alterações
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
