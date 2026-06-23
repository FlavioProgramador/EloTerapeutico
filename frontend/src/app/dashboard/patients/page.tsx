"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
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

interface Patient {
  id: number;
  full_name: string;
  cpf: string;
  formatted_cpf: string;
  phone: string;
  email: string;
  status: "active" | "inactive";
  age: number;
  is_active: boolean;
}

export default function PatientsListPage() {
  const router = useRouter();
  const { toast } = useToast();

  // Estados dos dados
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  // Estado do Modal de Cadastro
  const [isModalOpen, setIsModalOpen] = useState(false);
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

  // Busca lista de pacientes
  const fetchPatients = async () => {
    setIsLoading(true);
    try {
      const response = await api.get("patients/");
      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      setPatients(data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar pacientes",
        description: "Não foi possível carregar a lista de pacientes do servidor.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  // Monitora a data de nascimento para calcular menoridade
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

  const handleRegister = async (e: React.FormEvent) => {
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
      await api.post("patients/", payload);
      toast({
        title: "Paciente cadastrado!",
        description: "O paciente foi registrado com sucesso.",
        variant: "success",
      });
      setIsModalOpen(false);
      // Reseta Form
      setFormData({
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
      fetchPatients();
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

        toast({
          title: "Falha ao cadastrar",
          description: errorData?.message || "Corrija os erros apontados no formulário.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Falha ao cadastrar",
          description: "Ocorreu um erro ao salvar o registro no servidor.",
          variant: "destructive",
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Deseja realmente arquivar o cadastro do paciente "${name}"?`)) return;
    try {
      await api.delete(`patients/${id}/`);
      toast({
        title: "Paciente arquivado!",
        description: `O registro de ${name} foi desativado no sistema.`,
        variant: "success",
      });
      fetchPatients();
    } catch (err) {
      console.error(err);
      toast({
        title: "Erro ao arquivar",
        description: "Não foi possível excluir o paciente.",
        variant: "destructive",
      });
    }
  };

  // Filtra lista de pacientes no cliente
  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.cpf?.includes(searchTerm) ||
      p.phone?.includes(searchTerm);

    const matchesStatus =
      statusFilter === "all" ? true : p.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const activeCount = patients.filter((p) => p.status === "active").length;
  const inactiveCount = patients.filter((p) => p.status === "inactive").length;

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
          onClick={() => setIsModalOpen(true)}
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
              <h3 className="text-2xl font-bold text-foreground mt-1">{isLoading ? "..." : patients.length}</h3>
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
              <h3 className="text-2xl font-bold text-foreground mt-1">{isLoading ? "..." : activeCount}</h3>
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
              <h3 className="text-2xl font-bold text-foreground mt-1">{isLoading ? "..." : inactiveCount}</h3>
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
              onChange={(e) => setStatusFilter(e.target.value as any)}
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
        <div className="py-20 text-center flex flex-col items-center gap-2">
          <div className="h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-muted-foreground animate-pulse">Carregando pacientes...</span>
        </div>
      ) : filteredPatients.length === 0 ? (
        <Card className="border-border/80 bg-card shadow-xs p-12 text-center flex flex-col items-center justify-center gap-3">
          <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <h4 className="font-semibold text-sm text-foreground">Nenhum paciente encontrado</h4>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
              Não encontramos resultados correspondentes ao termo digitado ou ao filtro ativo.
            </p>
          </div>
        </Card>
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
              {filteredPatients.map((p) => (
                <TableRow key={p.id} className="cursor-pointer" onClick={() => router.push(`/dashboard/patients/${p.id}`)}>
                  <TableCell className="font-medium text-foreground">{p.full_name}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.formatted_cpf || "---"}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.age} anos</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{p.phone}</TableCell>
                  <TableCell>
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-sm text-[10px] font-semibold border ${
                        p.status === "active"
                          ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                          : "bg-secondary text-muted-foreground border-border"
                      }`}
                    >
                      {p.status === "active" ? "Ativo" : "Inativo"}
                    </span>
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
        <form onSubmit={handleRegister} className="space-y-4">
          <Input
            label="Nome Completo"
            placeholder="Nome completo do paciente"
            value={formData.fullName}
            onChange={(e) => handleInputChange("fullName", e.target.value)}
            error={errors.fullName}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="CPF"
              placeholder="000.000.000-00"
              value={formData.cpf}
              onChange={(e) => handleInputChange("cpf", e.target.value)}
              error={errors.cpf}
            />

            <Input
              label="Data de Nascimento"
              type="date"
              value={formData.birthDate}
              onChange={(e) => handleInputChange("birthDate", e.target.value)}
              error={errors.birthDate}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Gênero</label>
              <select
                value={formData.gender}
                onChange={(e) => handleInputChange("gender", e.target.value)}
                className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
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
            />
          </div>

          <Input
            label="E-mail"
            placeholder="paciente@email.com"
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange("email", e.target.value)}
            error={errors.email}
          />

          <Input
            label="Endereço Residencial"
            placeholder="Rua, Número, Bairro, Cidade..."
            value={formData.address}
            onChange={(e) => handleInputChange("address", e.target.value)}
            error={errors.address}
          />

          {/* Campos condicionais para Menores de 18 Anos */}
          {isMinor && (
            <div className="p-4 rounded-md border border-primary/20 bg-primary/5 space-y-4 animate-scale-in">
              <div className="flex items-center gap-2 text-primary font-semibold text-xs">
                <ShieldAlert className="h-4 w-4" />
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
              label="Indicação / Canal de Entrada"
              placeholder="Ex: Instagram, Google, Indicação"
              value={formData.referralSource}
              onChange={(e) => handleInputChange("referralSource", e.target.value)}
              error={errors.referralSource}
            />

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-muted-foreground">Status do Tratamento</label>
              <select
                value={formData.status}
                onChange={(e) => handleInputChange("status", e.target.value)}
                className="w-full h-10 bg-secondary border border-border rounded-md px-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 text-foreground cursor-pointer"
              >
                <option value="active">Ativo (Em Tratamento)</option>
                <option value="inactive">Inativo (Alta/Pausa)</option>
              </select>
            </div>
          </div>

          <Textarea
            label="Observações / Anotações Iniciais"
            placeholder="Queixas principais, histórico clínico rápido..."
            value={formData.notes}
            onChange={(e) => handleInputChange("notes", e.target.value)}
            error={errors.notes}
          />

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
