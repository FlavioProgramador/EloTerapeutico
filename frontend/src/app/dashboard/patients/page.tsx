"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Users,
  Search,
  Plus,
  Filter,
  UserCheck,
  UserMinus,
  Trash2,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

import { usePatients, useCreatePatient, useDeletePatient } from "@/features/patients/hooks/use-patients";
import { patientSchema, type PatientFormData } from "@/features/patients/schemas/patient.schemas";
import type { PatientStatus } from "@/types";

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

export default function PatientsListPage() {
  const router = useRouter();

  // Estados dos filtros e busca
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  // Estado do Modal de Cadastro
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Debounce da busca
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // React Query para buscar pacientes
  const {
    data: patientsData,
    isLoading,
    refetch,
  } = usePatients({
    search: debouncedSearch || undefined,
    status: statusFilter === "all" ? undefined : statusFilter,
  });

  const patientsList = patientsData?.results || [];

  // Mutações para criar e deletar
  const createPatientMutation = useCreatePatient();
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

  // Função para criar o paciente
  const onSubmit = async (data: PatientFormData) => {
    // Monta o payload
    const payload = {
      ...data,
      email: data.email || undefined,
      phone: data.phone || undefined,
      birth_date: data.birth_date || undefined,
      cpf: data.cpf || undefined,
      guardian_name: isMinor ? data.guardian_name : undefined,
      guardian_cpf: isMinor ? data.guardian_cpf : undefined,
      notes: data.notes || undefined,
      address: data.address ? { street: data.address } : undefined, // Ajustado ao formato esperado de JSON
      session_value: "0.00", // Valor padrão já que não é coletado no form principal
    };

    createPatientMutation.mutate(payload, {
      onSuccess: () => {
        setIsModalOpen(false);
        reset();
      },
      onError: (error: unknown) => {
        const errObj = error as { response?: { data?: { error?: { message?: string }; message?: string; detail?: string } } };
        const errorData = errObj.response?.data;
        if (errorData && typeof errorData === "object") {
          const apiError = errorData.error?.message || errorData.message || errorData.detail;
          toast.error("Falha ao cadastrar", {
            description: apiError || "Corrija os erros do formulário.",
          });
        }
      },
    });
  };

  // Função para deletar (arquivar) paciente
  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Deseja realmente arquivar o cadastro do paciente "${name}"?`)) return;
    deletePatientMutation.mutate(id, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  const activeCount = patientsList.filter((p) => p.status === "active").length;
  const inactiveCount = patientsList.filter((p) => p.status === "inactive").length;

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            CRM de Pacientes
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Gerencie prontuários, contatos e fichas cadastrais dos pacientes
          </p>
        </div>
        <Button
          onClick={() => {
            reset();
            setIsModalOpen(true);
          }}
          leftIcon={<Plus className="h-4 w-4" />}
          className="text-white font-semibold self-start sm:self-auto"
        >
          Novo Paciente
        </Button>
      </div>

      {/* Cards de Métricas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Total de Pacientes</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">
                {isLoading ? "..." : patientsList.length}
              </h3>
            </div>
            <div className="h-8 w-8 bg-primary/10 rounded-md flex items-center justify-center text-primary">
              <Users className="h-4.5 w-4.5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Em Tratamento (Ativos)</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">
                {isLoading ? "..." : activeCount}
              </h3>
            </div>
            <div className="h-8 w-8 bg-emerald-500/10 rounded-md flex items-center justify-center text-emerald-500">
              <UserCheck className="h-4.5 w-4.5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5 flex items-center justify-between">
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Altas / Inativos</p>
              <h3 className="text-2xl font-bold text-foreground mt-1">
                {isLoading ? "..." : inactiveCount}
              </h3>
            </div>
            <div className="h-8 w-8 bg-slate-500/10 rounded-md flex items-center justify-center text-slate-500">
              <UserMinus className="h-4.5 w-4.5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Barra de Filtros e Busca */}
      <Card className="border-border/80 bg-card shadow-xs p-4">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-muted-foreground/60" />
            <input
              type="text"
              placeholder="Buscar por nome, CPF ou telefone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full h-9 bg-secondary border border-border/60 rounded-md pl-10 pr-4 text-xs transition focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 placeholder:text-muted-foreground/50 text-foreground"
            />
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as "all" | "active" | "inactive")}
              className="h-9 bg-card border border-border/60 rounded-md px-3 text-xs focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
            >
              <option value="all">Todos os Status</option>
              <option value="active">Ativo (Em Tratamento)</option>
              <option value="inactive">Inativo (Alta/Pausa)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Listagem */}
      {isLoading ? (
        <SkeletonTable rows={5} />
      ) : patientsList.length === 0 ? (
        <EmptyState
          title="Nenhum paciente encontrado"
          description="Não encontramos resultados correspondentes ao termo digitado ou ao filtro ativo."
          icon={<Users className="h-6 w-6 text-muted-foreground" />}
          action={
            <Button
              onClick={() => {
                reset();
                setIsModalOpen(true);
              }}
              size="sm"
            >
              Cadastrar Paciente
            </Button>
          }
        />
      ) : (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Paciente</TableHead>
                <TableHead>CPF</TableHead>
                <TableHead>Idade</TableHead>
                <TableHead>Telefone</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {patientsList.map((p) => (
                <TableRow key={p.id} className="cursor-pointer" onClick={() => router.push(`/dashboard/patients/${p.id}`)}>
                  <TableCell className="font-medium text-foreground">{p.full_name}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.formatted_cpf || "---"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.age ? `${p.age} anos` : "---"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.phone || "---"}</TableCell>
                  <TableCell>
                    <Badge variant={p.status === "active" ? "success" : "muted"}>
                      {p.status === "active" ? "Ativo" : "Inativo"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground cursor-pointer"
                        onClick={() => router.push(`/dashboard/patients/${p.id}`)}
                        title="Ver prontuário"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-destructive/80 hover:text-destructive hover:bg-destructive/5 cursor-pointer"
                        onClick={() => handleDelete(p.id, p.full_name)}
                        title="Arquivar paciente"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Modal de Cadastro */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Cadastrar Novo Paciente"
        description="Preencha os dados cadastrais do novo paciente abaixo."
        className="max-w-xl"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="space-y-1">
            <Input
              id="patient-fullname"
              label="Nome Completo"
              placeholder="Nome completo do paciente"
              aria-invalid={!!errors.full_name}
              aria-describedby={errors.full_name ? "patient-fullname-error" : undefined}
              error={errors.full_name?.message}
              {...register("full_name")}
            />
            {errors.full_name && (
              <p id="patient-fullname-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.full_name.message}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="patient-cpf"
                label="CPF"
                placeholder="000.000.000-00"
                aria-invalid={!!errors.cpf}
                aria-describedby={errors.cpf ? "patient-cpf-error" : undefined}
                error={errors.cpf?.message}
                {...register("cpf", {
                  onChange: (e) => {
                    e.target.value = formatCPF(e.target.value);
                  }
                })}
              />
              {errors.cpf && (
                <p id="patient-cpf-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.cpf.message}
                </p>
              )}
            </div>

            <div className="space-y-1">
              <Input
                id="patient-birthdate"
                label="Data de Nascimento"
                type="date"
                aria-invalid={!!errors.birth_date}
                aria-describedby={errors.birth_date ? "patient-birthdate-error" : undefined}
                error={errors.birth_date?.message}
                {...register("birth_date")}
              />
              {errors.birth_date && (
                <p id="patient-birthdate-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.birth_date.message}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="patient-gender" className="text-xs font-semibold text-muted-foreground">Gênero</label>
              <select
                id="patient-gender"
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
                id="patient-phone"
                label="Telefone / WhatsApp"
                placeholder="(11) 99999-9999"
                aria-invalid={!!errors.phone}
                aria-describedby={errors.phone ? "patient-phone-error" : undefined}
                error={errors.phone?.message}
                {...register("phone", {
                  onChange: (e) => {
                    e.target.value = formatPhone(e.target.value);
                  }
                })}
              />
              {errors.phone && (
                <p id="patient-phone-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.phone.message}
                </p>
              )}
            </div>
          </div>

          <div className="space-y-1">
            <Input
              id="patient-email"
              label="E-mail"
              placeholder="paciente@email.com"
              type="email"
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "patient-email-error" : undefined}
              error={errors.email?.message}
              {...register("email")}
            />
            {errors.email && (
              <p id="patient-email-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.email.message}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <Input
              id="patient-address"
              label="Endereço Residencial"
              placeholder="Rua, Número, Bairro, Cidade..."
              aria-invalid={!!errors.address}
              aria-describedby={errors.address ? "patient-address-error" : undefined}
              error={errors.address?.message}
              {...register("address")}
            />
            {errors.address && (
              <p id="patient-address-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.address.message}
              </p>
            )}
          </div>

          {/* Campos condicionais para Menores de 18 Anos */}
          {isMinor && (
            <div className="p-4 rounded-md border border-primary/20 bg-primary/5 space-y-4 animate-scale-in">
              <div className="flex items-center gap-2 text-primary font-semibold text-xs">
                <ShieldAlert className="h-4 w-4" />
                <span>Paciente Menor de Idade (Requer Responsável)</span>
              </div>

              <div className="space-y-1">
                <Input
                  id="patient-guardianname"
                  label="Nome do Responsável Legal"
                  placeholder="Nome completo do pai, mãe ou tutor"
                  aria-invalid={!!errors.guardian_name}
                  aria-describedby={errors.guardian_name ? "patient-guardianname-error" : undefined}
                  error={errors.guardian_name?.message}
                  {...register("guardian_name")}
                  className="bg-card"
                />
                {errors.guardian_name && (
                  <p id="patient-guardianname-error" className="text-xs text-destructive animate-fade-in" role="alert">
                    {errors.guardian_name.message}
                  </p>
                )}
              </div>

              <div className="space-y-1">
                <Input
                  id="patient-guardiancpf"
                  label="CPF do Responsável Legal"
                  placeholder="000.000.000-00"
                  aria-invalid={!!errors.guardian_cpf}
                  aria-describedby={errors.guardian_cpf ? "patient-guardiancpf-error" : undefined}
                  error={errors.guardian_cpf?.message}
                  {...register("guardian_cpf", {
                    onChange: (e) => {
                      e.target.value = formatCPF(e.target.value);
                    }
                  })}
                  className="bg-card"
                />
                {errors.guardian_cpf && (
                  <p id="patient-guardiancpf-error" className="text-xs text-destructive animate-fade-in" role="alert">
                    {errors.guardian_cpf.message}
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <Input
                id="patient-referral"
                label="Indicação / Canal de Entrada"
                placeholder="Ex: Instagram, Google, Indicação"
                aria-invalid={!!errors.referral_source}
                aria-describedby={errors.referral_source ? "patient-referral-error" : undefined}
                error={errors.referral_source?.message}
                {...register("referral_source")}
              />
              {errors.referral_source && (
                <p id="patient-referral-error" className="text-xs text-destructive animate-fade-in" role="alert">
                  {errors.referral_source.message}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="patient-status" className="text-xs font-semibold text-muted-foreground">Status do Tratamento</label>
              <select
                id="patient-status"
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
              id="patient-notes"
              label="Observações / Anotações Iniciais"
              placeholder="Queixas principais, histórico clínico rápido..."
              aria-invalid={!!errors.notes}
              aria-describedby={errors.notes ? "patient-notes-error" : undefined}
              error={errors.notes?.message}
              {...register("notes")}
            />
            {errors.notes && (
              <p id="patient-notes-error" className="text-xs text-destructive animate-fade-in" role="alert">
                {errors.notes.message}
              </p>
            )}
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsModalOpen(false)}
              className="px-4"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              className="px-4 text-white font-semibold"
            >
              Registrar Paciente
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
