"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
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
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";

interface PatientDetail {
  id: number;
  full_name: string;
  cpf: string;
  formatted_cpf: string;
  birth_date: string;
  gender: string;
  email: string;
  phone: string;
  address: string;
  status: "active" | "inactive";
  referral_source: string;
  guardian_name: string;
  guardian_cpf: string;
  notes: string;
  age: number;
  created_at: string;
}

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const patientId = params.id;

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Estados do Modal de Edição
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isMinor, setIsMinor] = useState(false);

  const [formData, setFormData] = useState({
    fullName: "",
    cpf: "",
    birthDate: "",
    gender: "M",
    email: "",
    phone: "",
    address: "",
    status: "active",
    referralSource: "",
    guardianName: "",
    guardianCpf: "",
    notes: "",
  });

  const fetchPatientDetail = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<PatientDetail>(`patients/${patientId}/`);
      setPatient(response.data);
      
      // Carrega os dados no form de edição
      setFormData({
        fullName: response.data.full_name,
        cpf: response.data.cpf || "",
        birthDate: response.data.birth_date || "",
        gender: response.data.gender || "M",
        email: response.data.email || "",
        phone: response.data.phone || "",
        address: response.data.address || "",
        status: response.data.status,
        referralSource: response.data.referral_source || "",
        guardianName: response.data.guardian_name || "",
        guardianCpf: response.data.guardian_cpf || "",
        notes: response.data.notes || "",
      });
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar detalhes",
        description: "Não foi possível carregar as informações do paciente.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) {
      fetchPatientDetail();
    }
  }, [patientId]);

  // Monitora menoridade
  useEffect(() => {
    if (!formData.birthDate) {
      setIsMinor(false);
      return;
    }
    try {
      const birth = new Date(formData.birthDate);
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
  }, [formData.birthDate]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validateForm = () => {
    const tempErrors: Record<string, string> = {};
    if (!formData.fullName.trim()) tempErrors.fullName = "Nome completo é obrigatório";
    if (!formData.phone.trim()) tempErrors.phone = "Telefone é obrigatório";
    if (!formData.birthDate) tempErrors.birthDate = "Data de nascimento é obrigatória";

    if (isMinor) {
      if (!formData.guardianName.trim()) {
        tempErrors.guardianName = "Nome do responsável legal é obrigatório para menores";
      }
      if (!formData.guardianCpf.trim()) {
        tempErrors.guardianCpf = "CPF do responsável legal é obrigatório para menores";
      }
    }

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);

    const payload = {
      full_name: formData.fullName,
      cpf: formData.cpf,
      birth_date: formData.birthDate,
      gender: formData.gender,
      email: formData.email || null,
      phone: formData.phone,
      address: formData.address || null,
      status: formData.status,
      referral_source: formData.referralSource || null,
      guardian_name: isMinor ? formData.guardianName : null,
      guardian_cpf: isMinor ? formData.guardianCpf : null,
      notes: formData.notes || null,
    };

    try {
      await api.put(`patients/${patientId}/`, payload);
      toast({
        title: "Ficha atualizada!",
        description: "Os dados do paciente foram salvos com sucesso.",
        variant: "success",
      });
      setIsEditModalOpen(false);
      fetchPatientDetail();
    } catch (error: any) {
      console.error(error);
      const errorData = error.response?.data?.error;
      const serverErrors = errorData?.details || error.response?.data;
      if (serverErrors && typeof serverErrors === "object") {
        const fieldErrors: Record<string, string> = {};
        Object.entries(serverErrors).forEach(([key, value]) => {
          const fieldMap: Record<string, string> = {
            full_name: "fullName",
            cpf: "cpf",
            birth_date: "birthDate",
            gender: "gender",
            email: "email",
            phone: "phone",
            address: "address",
            status: "status",
            referral_source: "referralSource",
            guardian_name: "guardianName",
            guardian_cpf: "guardianCpf",
            notes: "notes",
          };
          const mappedKey = fieldMap[key] || key;
          fieldErrors[mappedKey] = Array.isArray(value) ? value[0] : String(value);
        });
        setErrors(fieldErrors);
      } else {
        toast({
          title: "Falha ao editar",
          description: "Ocorreu um erro ao atualizar os dados.",
          variant: "destructive",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleArchive = async () => {
    if (!confirm(`Deseja realmente arquivar o cadastro do paciente "${patient?.full_name}"?`)) return;
    try {
      await api.delete(`patients/${patientId}/`);
      toast({
        title: "Paciente arquivado!",
        description: "O cadastro do paciente foi desativado no sistema.",
        variant: "success",
      });
      router.push("/dashboard/patients");
    } catch (err) {
      console.error(err);
      toast({
        title: "Erro ao arquivar",
        description: "Não foi possível excluir o paciente.",
        variant: "destructive",
      });
    }
  };

  const getGenderLabel = (g: string) => {
    const genders: Record<string, string> = {
      M: "Masculino",
      F: "Feminino",
      O: "Outro",
    };
    return genders[g] || g;
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-3">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="text-sm text-muted-foreground animate-pulse">Carregando ficha...</span>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="py-20 text-center flex flex-col items-center gap-4">
        <ShieldAlert className="h-10 w-10 text-destructive" />
        <div>
          <h3 className="font-bold text-lg">Paciente não encontrado</h3>
          <p className="text-sm text-muted-foreground mt-1">
            O registro solicitado não existe ou foi removido do sistema.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.push("/dashboard/patients")}>
          Voltar para CRM
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Botão Voltar */}
      <button
        onClick={() => router.push("/dashboard/patients")}
        className="flex items-center gap-2 text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <ArrowLeft className="h-4.5 w-4.5" />
        Voltar para lista de pacientes
      </button>

      {/* Header Ficha */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-border/40 pb-6">
        <div className="flex items-start gap-4">
          <div className="h-14 w-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-xl uppercase shrink-0">
            {patient.full_name.charAt(0)}
          </div>
          <div className="space-y-1">
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
              {patient.full_name}
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span>Cadastrado em {new Date(patient.created_at).toLocaleDateString("pt-BR")}</span>
              <span>•</span>
              <span
                className={`inline-flex px-2 py-0.5 rounded-full font-semibold border ${
                  patient.status === "active"
                    ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                    : "bg-slate-500/10 text-slate-500 border-slate-500/20"
                }`}
              >
                {patient.status === "active" ? "Em Tratamento" : "Alta/Inativo"}
              </span>
            </div>
          </div>
        </div>

        {/* Ações */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="sm"
            onClick={() => router.push(`/dashboard/records/${patient.id}`)}
            leftIcon={<ClipboardList className="h-4.5 w-4.5" />}
            className="text-white font-semibold"
          >
            Ver Prontuário
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-border hover:bg-secondary/60 text-foreground"
            onClick={() => setIsEditModalOpen(true)}
            leftIcon={<Edit2 className="h-4.5 w-4.5" />}
          >
            Editar Cadastro
          </Button>
          <Button
            size="sm"
            variant="glass"
            className="border-destructive/20 text-destructive hover:bg-destructive/10 cursor-pointer"
            onClick={handleArchive}
            leftIcon={<Trash2 className="h-4.5 w-4.5" />}
          >
            Arquivar
          </Button>
        </div>
      </div>

      {/* Grid Dados */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Ficha Geral */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border/30 bg-card/65 backdrop-blur-md">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Info className="h-5 w-5 text-primary" />
                Dados Cadastrais
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-6 mt-3">
              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Nome Completo</p>
                <p className="text-base font-semibold">{patient.full_name}</p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">CPF</p>
                <p className="text-base font-semibold">{patient.formatted_cpf || "---"}</p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Data de Nascimento</p>
                <p className="text-base font-semibold flex items-center gap-2">
                  <CalendarDays className="h-4.5 w-4.5 text-muted-foreground" />
                  <span>{patient.birth_date ? new Date(patient.birth_date).toLocaleDateString("pt-BR") : "---"} ({patient.age} anos)</span>
                </p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Gênero</p>
                <p className="text-base font-semibold">{getGenderLabel(patient.gender)}</p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Indicação / Origem</p>
                <p className="text-base font-semibold">{patient.referral_source || "Nenhuma informada"}</p>
              </div>

              <div className="space-y-1">
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Terapeuta Responsável</p>
                <p className="text-base font-semibold flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-muted-foreground" />
                  <span>{patient.therapist_name}</span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Notas Clínicas de Entrada */}
          <Card className="border-border/30 bg-card/65 backdrop-blur-md">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-lg font-bold flex items-center gap-2">
                <Heart className="h-5 w-5 text-emerald-500" />
                Notas de Entrada / Queixa Principal
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 mt-3">
              {patient.notes ? (
                <p className="text-base text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {patient.notes}
                </p>
              ) : (
                <p className="text-sm text-muted-foreground italic">
                  Nenhuma anotação ou queixa inicial informada no cadastro.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Lateral: Contato & Responsável Legal */}
        <div className="space-y-6">
          {/* Informações de Contato */}
          <Card className="border-border/30 bg-card/65 backdrop-blur-md">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base font-bold">Informações de Contato</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4 mt-3">
              <div className="flex items-start gap-3">
                <Phone className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-muted-foreground uppercase">WhatsApp / Telefone</p>
                  <a href={`tel:${patient.phone}`} className="text-sm font-semibold hover:underline">
                    {patient.phone}
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Mail className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-muted-foreground uppercase">E-mail</p>
                  {patient.email ? (
                    <a href={`mailto:${patient.email}`} className="text-sm font-semibold hover:underline truncate max-w-[200px] block">
                      {patient.email}
                    </a>
                  ) : (
                    <span className="text-sm text-muted-foreground">Não cadastrado</span>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-muted-foreground uppercase">Endereço Residencial</p>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {patient.address || "Não informado"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Responsável Legal (Condicional) */}
          {patient.age < 18 ? (
            <Card className="border-primary/20 bg-primary/5 backdrop-blur-md relative overflow-hidden">
              <div className="absolute top-0 left-0 h-full w-[4px] bg-primary" />
              <CardHeader className="pb-3 border-b border-primary/10">
                <CardTitle className="text-base font-bold flex items-center gap-2 text-foreground">
                  <ShieldAlert className="h-5 w-5 text-primary shrink-0" />
                  Responsável Legal
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-3.5 mt-3">
                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-muted-foreground uppercase">Nome do Tutor</p>
                  <p className="text-sm font-semibold">{patient.guardian_name || "---"}</p>
                </div>

                <div className="space-y-0.5">
                  <p className="text-xs font-bold text-muted-foreground uppercase">CPF do Tutor</p>
                  <p className="text-sm font-semibold">{patient.guardian_cpf || "---"}</p>
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
        <form onSubmit={handleEdit} className="space-y-4">
          <Input
            label="Nome Completo"
            placeholder="Nome completo do paciente"
            value={formData.fullName}
            onChange={(e) => handleInputChange("fullName", e.target.value)}
            error={errors.fullName}
            className="bg-secondary/20"
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="CPF"
              placeholder="000.000.000-00"
              value={formData.cpf}
              onChange={(e) => handleInputChange("cpf", e.target.value)}
              error={errors.cpf}
              className="bg-secondary/20"
            />

            <Input
              label="Data de Nascimento"
              type="date"
              value={formData.birthDate}
              onChange={(e) => handleInputChange("birthDate", e.target.value)}
              error={errors.birthDate}
              className="bg-secondary/20"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Gênero</label>
              <select
                value={formData.gender}
                onChange={(e) => handleInputChange("gender", e.target.value)}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="M">Masculino</option>
                <option value="F">Feminino</option>
                <option value="O">Outro</option>
              </select>
            </div>

            <Input
              label="Telefone / WhatsApp"
              placeholder="(11) 99999-9999"
              value={formData.phone}
              onChange={(e) => handleInputChange("phone", e.target.value)}
              error={errors.phone}
              className="bg-secondary/20"
            />
          </div>

          <Input
            label="E-mail"
            placeholder="paciente@email.com"
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange("email", e.target.value)}
            error={errors.email}
            className="bg-secondary/20"
          />

          <Input
            label="Endereço Residencial"
            placeholder="Rua, Número, Bairro, Cidade..."
            value={formData.address}
            onChange={(e) => handleInputChange("address", e.target.value)}
            error={errors.address}
            className="bg-secondary/20"
          />

          {/* Responsável se Menor */}
          {isMinor && (
            <div className="p-4 rounded-xl border border-primary/20 bg-primary/5 space-y-4 animate-scale-in">
              <div className="flex items-center gap-2 text-primary font-semibold text-sm">
                <ShieldAlert className="h-4.5 w-4.5" />
                <span>Paciente Menor de Idade (Requer Responsável)</span>
              </div>

              <Input
                label="Nome do Responsável Legal"
                placeholder="Nome completo do pai, mãe ou tutor"
                value={formData.guardianName}
                onChange={(e) => handleInputChange("guardianName", e.target.value)}
                error={errors.guardianName}
                className="bg-card"
              />

              <Input
                label="CPF do Responsável Legal"
                placeholder="000.000.000-00"
                value={formData.guardianCpf}
                onChange={(e) => handleInputChange("guardianCpf", e.target.value)}
                error={errors.guardianCpf}
                className="bg-card"
              />
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Indicação / Origem"
              placeholder="Ex: Instagram, Médico X"
              value={formData.referralSource}
              onChange={(e) => handleInputChange("referralSource", e.target.value)}
              error={errors.referralSource}
              className="bg-secondary/20"
            />

            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Status do Tratamento</label>
              <select
                value={formData.status}
                onChange={(e) => handleInputChange("status", e.target.value)}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="active">Ativo (Em Tratamento)</option>
                <option value="inactive">Inativo</option>
              </select>
            </div>
          </div>

          <Textarea
            label="Observações / Anotações Iniciais"
            placeholder="Histórico rápido, queixas clínicas..."
            value={formData.notes}
            onChange={(e) => handleInputChange("notes", e.target.value)}
            error={errors.notes}
            className="bg-secondary/20"
          />

          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsEditModalOpen(false)}
              className="px-5 border-border text-foreground"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              className="px-5 text-white font-semibold"
            >
              Salvar Alterações
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
