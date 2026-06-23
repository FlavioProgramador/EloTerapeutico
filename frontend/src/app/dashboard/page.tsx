"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Users,
  Calendar,
  DollarSign,
  TrendingUp,
  Activity,
  Plus,
  Check,
  X,
  Clock,
  ArrowRight,
  ChevronRight,
  AlertCircle,
  AlertTriangle,
  UserCheck,
} from "lucide-react";
import { useAuth } from "@/contexts/auth";
import { useToast } from "@/contexts/toast";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Appointment {
  id: number;
  patient_name: string;
  therapist_name: string;
  start_time: string;
  end_time: string;
  duration_display: string;
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show";
  status_display: string;
  session_value: string;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  // Estados dos dados da API
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patientCount, setPatientCount] = useState<number>(0);
  const [monthlyRevenue, setMonthlyRevenue] = useState<number>(0);
  const [pendingTransactions, setPendingTransactions] = useState<number>(0);
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Busca todos os dados necessários da API
  const fetchDashboardData = async () => {
    setIsLoadingData(true);
    try {
      // 1. Busca consultas de hoje
      const appointmentsResponse = await api.get<Appointment[]>("agenda/appointments/today/");
      setAppointments(appointmentsResponse.data);

      // 2. Busca pacientes para contar total (tratando paginação básica ou fallback)
      try {
        const patientsResponse = await api.get("patients/");
        // DRF pode retornar { count, results } ou direto []
        const count = Array.isArray(patientsResponse.data) 
          ? patientsResponse.data.length 
          : patientsResponse.data.count || patientsResponse.data.results?.length || 0;
        setPatientCount(count);
      } catch (err) {
        console.error("Erro ao carregar pacientes:", err);
      }

      // 3. Busca transações do mês corrente para calcular faturamento mensal
      try {
        const financeResponse = await api.get("financeiro/");
        const transactions = Array.isArray(financeResponse.data)
          ? financeResponse.data
          : financeResponse.data.results || [];
        
        let revenue = 0;
        let pending = 0;

        transactions.forEach((tx: any) => {
          const amount = parseFloat(tx.amount || 0);
          if (tx.transaction_type === "income" && tx.payment_status === "paid") {
            revenue += amount;
          }
          if (tx.payment_status === "pending") {
            pending += amount;
          }
        });

        setMonthlyRevenue(revenue);
        setPendingTransactions(pending);
      } catch (err) {
        console.error("Erro ao carregar dados financeiros:", err);
      }

    } catch (error) {
      console.error("Erro ao carregar painel:", error);
      toast({
        title: "Erro de Sincronização",
        description: "Não foi possível carregar as informações em tempo real do servidor.",
        variant: "destructive",
      });
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Alteração rápida de status da consulta
  const handleUpdateStatus = async (appointmentId: number, newStatus: string, statusLabel: string) => {
    try {
      await api.patch(`agenda/appointments/${appointmentId}/status/`, {
        status: newStatus,
      });
      
      toast({
        title: `Consulta ${statusLabel}`,
        description: "O status do agendamento foi atualizado com sucesso.",
        variant: "success",
      });
      
      // Atualiza a listagem de hoje localmente
      fetchDashboardData();
    } catch (error: any) {
      console.error(error);
      toast({
        title: "Falha na atualização",
        description: "Não foi possível alterar o status da consulta.",
        variant: "destructive",
      });
    }
  };

  // Formatação de Horário (ISO string para HH:MM)
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "--:--";
    }
  };

  // Cores de Badge por Status
  const getStatusBadgeClass = (status: string) => {
    const classes = {
      scheduled: "bg-blue-500/10 text-blue-500 border-blue-500/20",
      confirmed: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
      completed: "bg-slate-500/10 text-slate-500 border-slate-500/20",
      cancelled: "bg-destructive/10 text-destructive border-destructive/20",
      no_show: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    };
    return classes[status as keyof typeof classes] || "bg-secondary text-muted-foreground";
  };

  return (
    <div className="space-y-8">
      {/* Cabeçalho de Boas-Vindas */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground/90 to-foreground/80">
            Olá, {user?.full_name?.split(" ")[0] || "Terapeuta"}!
          </h1>
          <p className="text-muted-foreground mt-1">
            Aqui está o resumo da sua clínica para o dia de hoje.
          </p>
        </div>
        
        {/* Ações Rápidas de Topo */}
        <div className="flex items-center gap-3">
          <Button
            size="sm"
            onClick={() => router.push("/dashboard/patients")}
            leftIcon={<Plus className="h-4.5 w-4.5" />}
          >
            Cadastrar Paciente
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-border/60 hover:bg-secondary/40"
            onClick={() => router.push("/dashboard/agenda")}
            leftIcon={<Calendar className="h-4.5 w-4.5" />}
          >
            Agendar Sessão
          </Button>
        </div>
      </div>

      {/* Grid de Cards de Indicadores (KPIs) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="hover-glow bg-card/65 backdrop-blur-md relative overflow-hidden border-border/30">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-primary" />
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Pacientes Ativos
              </p>
              <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                <Users className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-3xl font-bold tracking-tight">
                {isLoadingData ? "..." : patientCount}
              </h3>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
                <span>Cadastrados no sistema</span>
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-glow bg-card/65 backdrop-blur-md relative overflow-hidden border-border/30">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-indigo-500" />
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Consultas Hoje
              </p>
              <div className="h-9 w-9 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-500">
                <Calendar className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-3xl font-bold tracking-tight">
                {isLoadingData ? "..." : appointments.length}
              </h3>
              <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-indigo-500" />
                <span>Horários agendados</span>
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-glow bg-card/65 backdrop-blur-md relative overflow-hidden border-border/30">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-emerald-500" />
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Faturamento (Mês)
              </p>
              <div className="h-9 w-9 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-3xl font-bold tracking-tight">
                {isLoadingData ? "..." : `R$ ${monthlyRevenue.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              </h3>
              <p className="text-xs text-emerald-500 mt-1 flex items-center gap-1 font-semibold">
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Receita confirmada</span>
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="hover-glow bg-card/65 backdrop-blur-md relative overflow-hidden border-border/30">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-amber-500" />
          <CardContent className="p-6">
            <div className="flex justify-between items-start">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                A Receber / Pendente
              </p>
              <div className="h-9 w-9 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
            <div className="mt-4">
              <h3 className="text-3xl font-bold tracking-tight">
                {isLoadingData ? "..." : `R$ ${pendingTransactions.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              </h3>
              <p className="text-xs text-amber-500 mt-1 flex items-center gap-1 font-semibold">
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Aguardando liquidação</span>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Grid Principal - Agenda & Links de Atalho */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Agenda do Dia */}
        <Card className="lg:col-span-2 bg-card/65 backdrop-blur-md border-border/30">
          <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-border/40">
            <div>
              <CardTitle className="text-lg font-bold">Agenda de Hoje</CardTitle>
              <CardDescription>
                Consulte e alterne os status dos atendimentos abaixo
              </CardDescription>
            </div>
            <span className="text-xs font-semibold text-muted-foreground bg-secondary/80 px-2.5 py-1 rounded-full">
              {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "short" })}
            </span>
          </CardHeader>
          
          <CardContent className="p-6">
            {isLoadingData ? (
              <div className="py-12 flex flex-col items-center justify-center gap-3">
                <Activity className="h-8 w-8 text-primary animate-spin" />
                <span className="text-sm text-muted-foreground animate-pulse">Buscando consultas...</span>
              </div>
            ) : appointments.length === 0 ? (
              <div className="py-12 text-center flex flex-col items-center justify-center gap-4">
                <div className="h-12 w-12 rounded-full bg-secondary/50 flex items-center justify-center text-muted-foreground">
                  <Calendar className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-bold text-base text-foreground">Sem consultas hoje</h4>
                  <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                    Sua agenda para o dia está livre. Clique abaixo para agendar um novo atendimento.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-border hover:bg-secondary/60 mt-2"
                  onClick={() => router.push("/dashboard/agenda")}
                >
                  Criar Novo Agendamento
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {appointments.map((appt) => (
                  <div
                    key={appt.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-border/40 bg-card hover:bg-secondary/15 transition-all duration-200 gap-4"
                  >
                    <div className="flex items-start gap-4">
                      {/* Horário da Consulta */}
                      <div className="flex flex-col items-center justify-center bg-secondary/80 rounded-lg p-2.5 min-w-[70px] text-center border border-border/30">
                        <Clock className="h-4 w-4 text-muted-foreground mb-1" />
                        <span className="font-bold text-sm text-foreground">
                          {formatTime(appt.start_time)}
                        </span>
                      </div>

                      {/* Dados da Consulta */}
                      <div className="space-y-1">
                        <h4 className="font-bold text-base text-foreground">
                          {appt.patient_name}
                        </h4>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span>Com {appt.therapist_name}</span>
                          <span>•</span>
                          <span>Valor: R$ {parseFloat(appt.session_value).toFixed(2)}</span>
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-full text-[10px] font-semibold border",
                              getStatusBadgeClass(appt.status)
                            )}
                          >
                            {appt.status_display}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Ações Rápidas sobre a Consulta */}
                    <div className="flex items-center gap-2 sm:ml-auto self-end sm:self-center">
                      {appt.status === "scheduled" && (
                        <>
                          <Button
                            size="sm"
                            variant="glass"
                            className="h-8 px-2.5 text-xs text-emerald-500 border-emerald-500/20 hover:bg-emerald-500/10 cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "confirmed", "Confirmada")}
                            leftIcon={<Check className="h-3.5 w-3.5" />}
                          >
                            Confirmar
                          </Button>
                          <Button
                            size="sm"
                            variant="glass"
                            className="h-8 px-2.5 text-xs text-destructive border-destructive/20 hover:bg-destructive/10 cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "cancelled", "Cancelada")}
                            leftIcon={<X className="h-3.5 w-3.5" />}
                          >
                            Cancelar
                          </Button>
                        </>
                      )}
                      
                      {appt.status === "confirmed" && (
                        <>
                          <Button
                            size="sm"
                            variant="glass"
                            className="h-8 px-2.5 text-xs text-slate-500 border-slate-500/20 hover:bg-slate-500/10 cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "completed", "Concluída")}
                            leftIcon={<UserCheck className="h-3.5 w-3.5" />}
                          >
                            Concluir
                          </Button>
                          <Button
                            size="sm"
                            variant="glass"
                            className="h-8 px-2.5 text-xs text-amber-500 border-amber-500/20 hover:bg-amber-500/10 cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "no_show", "Falta Registrada")}
                            leftIcon={<AlertTriangle className="h-3.5 w-3.5" />}
                          >
                            Faltou
                          </Button>
                        </>
                      )}

                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground cursor-pointer"
                        onClick={() => router.push(`/dashboard/patients/${appt.id}`)}
                        title="Ver prontuário do paciente"
                      >
                        <ChevronRight className="h-4.5 w-4.5" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Atalhos rápidos & Segurança */}
        <div className="space-y-6">
          {/* Ações Rápidas */}
          <Card className="bg-card/65 backdrop-blur-md border-border/30">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base font-bold">Atalhos Clínicos</CardTitle>
              <CardDescription>Acesse rapidamente as rotas mais usadas</CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-2 mt-2">
              <button
                onClick={() => router.push("/dashboard/patients")}
                className="w-full flex items-center justify-between p-3.5 rounded-lg border border-border/30 bg-card hover:bg-secondary/40 text-left transition-all group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-primary" />
                  <div className="text-sm font-semibold">CRM de Pacientes</div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
              </button>

              {user && (user.role === "therapist" || user.role === "admin") && (
                <button
                  onClick={() => router.push("/dashboard/records")}
                  className="w-full flex items-center justify-between p-3.5 rounded-lg border border-border/30 bg-card hover:bg-secondary/40 text-left transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Activity className="h-5 w-5 text-indigo-500" />
                    <div className="text-sm font-semibold">Prontuário Eletrônico</div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                </button>
              )}

              <button
                onClick={() => router.push("/dashboard/agenda")}
                className="w-full flex items-center justify-between p-3.5 rounded-lg border border-border/30 bg-card hover:bg-secondary/40 text-left transition-all group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-emerald-500" />
                  <div className="text-sm font-semibold">Calendário Completo</div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                onClick={() => router.push("/dashboard/financeiro")}
                className="w-full flex items-center justify-between p-3.5 rounded-lg border border-border/30 bg-card hover:bg-secondary/40 text-left transition-all group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <DollarSign className="h-5 w-5 text-amber-500" />
                  <div className="text-sm font-semibold">Fluxo Financeiro</div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
              </button>
            </CardContent>
          </Card>

          {/* Dica de Segurança / Conformidade LGPD */}
          <Card className="bg-primary/5 border-primary/20 backdrop-blur-md relative overflow-hidden">
            <div className="absolute top-0 left-0 h-full w-[4px] bg-primary" />
            <CardContent className="p-5 flex gap-4">
              <AlertCircle className="h-6 w-6 text-primary shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h5 className="font-bold text-sm text-foreground">Conformidade LGPD</h5>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Todos os prontuários e evoluções de pacientes são criptografados de ponta a ponta na nuvem. Mantenha suas credenciais seguras e não compartilhe seu login.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
