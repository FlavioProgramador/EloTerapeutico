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
  Percent,
  ClipboardCheck,
  TrendingDown,
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
  status: "scheduled" | "confirmed" | "completed" | "cancelled" | "no_show" | "missed";
  status_display: string;
  session_value: string;
}

interface Evolution {
  id: number;
  patient: number;
  session_date: string;
  is_locked: boolean;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const router = useRouter();

  // Estados dos dados da API
  const [appointmentsToday, setAppointmentsToday] = useState<Appointment[]>([]);
  const [patientCount, setPatientCount] = useState<number>(0);
  
  // KPIs Clínicos Calculados
  const [occupancyRate, setOccupancyRate] = useState<number>(0);
  const [occupiedHours, setOccupiedHours] = useState<number>(0);
  const [weeklyTarget, setWeeklyTarget] = useState<number>(30); // Grade padrão de 30h
  const [pendingEvolutionsCount, setPendingEvolutionsCount] = useState<number>(0);
  const [faturamentoFaturado, setFaturamentoFaturado] = useState<number>(0);
  const [faturamentoRecebido, setFaturamentoRecebido] = useState<number>(0);
  const [absenteismoRate, setAbsenteismoRate] = useState<number>(0);
  const [missedCount, setMissedCount] = useState<number>(0);
  const [totalPastSessions, setTotalPastSessions] = useState<number>(0);

  const [isLoadingData, setIsLoadingData] = useState(true);

  // Busca todos os dados necessários da API e calcula KPIs
  const fetchDashboardData = async () => {
    setIsLoadingData(true);
    try {
      const now = new Date();

      // 1. Busca consultas de hoje
      const appointmentsTodayResponse = await api.get<Appointment[]>("agenda/appointments/today/");
      setAppointmentsToday(appointmentsTodayResponse.data);

      // 2. Contar pacientes
      try {
        const patientsResponse = await api.get("patients/");
        const count = Array.isArray(patientsResponse.data) 
          ? patientsResponse.data.length 
          : patientsResponse.data.count || patientsResponse.data.results?.length || 0;
        setPatientCount(count);
      } catch (err) {
        console.error("Erro ao carregar pacientes:", err);
      }

      // 3. Buscar consultas do mês para ocupação e absenteísmo
      const year = now.getFullYear();
      const month = now.getMonth();
      const startOfMonth = new Date(year, month, 1).toISOString();
      const endOfMonth = new Date(year, month + 1, 0, 23, 59, 59).toISOString();

      let monthlyAppointments: Appointment[] = [];
      try {
        const appointmentsResponse = await api.get("agenda/appointments/", {
          params: {
            start_time_gte: startOfMonth,
            start_time_lte: endOfMonth,
          },
        });
        monthlyAppointments = Array.isArray(appointmentsResponse.data)
          ? appointmentsResponse.data
          : (appointmentsResponse.data as any).results || [];
      } catch (err) {
        console.error("Erro ao carregar consultas do mês:", err);
      }

      // 4. Buscar evoluções para conformidade CFP
      let evolutions: Evolution[] = [];
      if (user?.role === "therapist" || user?.role === "admin") {
        try {
          const evolutionsResponse = await api.get("records/evolutions/");
          evolutions = Array.isArray(evolutionsResponse.data)
            ? evolutionsResponse.data
            : (evolutionsResponse.data as any).results || [];
        } catch (err) {
          console.error("Erro ao carregar evoluções:", err);
        }
      }

      // 5. Buscar transações do mês para financeiro faturado vs líquido recebido
      try {
        const financeResponse = await api.get("financeiro/");
        const transactions = Array.isArray(financeResponse.data)
          ? financeResponse.data
          : financeResponse.data.results || [];
        
        let faturado = 0;
        let recebido = 0;

        transactions.forEach((tx: any) => {
          const amount = parseFloat(tx.amount || 0);
          const txDate = new Date(tx.date || tx.created_at);
          // Apenas transações deste mês
          if (txDate.getMonth() === month && txDate.getFullYear() === year) {
            if (tx.transaction_type === "income") {
              faturado += amount;
              if (tx.payment_status === "paid") {
                recebido += amount;
              }
            }
          }
        });

        setFaturamentoFaturado(faturado);
        setFaturamentoRecebido(recebido);
      } catch (err) {
        console.error("Erro ao carregar dados financeiros:", err);
      }

      // ───────────────────────────────────────────────────────────────────────
      // CÁLCULOS DOS INDICADORES
      // ───────────────────────────────────────────────────────────────────────
      
      // A. Ocupação Semanal (consultas ativas na semana atual)
      const startOfWeek = new Date(now);
      const day = startOfWeek.getDay();
      const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1); // Segunda-feira
      startOfWeek.setDate(diff);
      startOfWeek.setHours(0, 0, 0, 0);

      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6); // Domingo
      endOfWeek.setHours(23, 59, 59, 999);

      const weeklyAppts = monthlyAppointments.filter(appt => {
        const d = new Date(appt.start_time);
        return d >= startOfWeek && d <= endOfWeek && appt.status !== "cancelled";
      });

      const hours = weeklyAppts.length; // Cada consulta dura 50 min/1h aprox
      setOccupiedHours(hours);
      const target = 30; // Grade padrão de 30 consultas/semana
      setWeeklyTarget(target);
      setOccupancyRate(Math.min(Math.round((hours / target) * 100), 100));

      // B. Absenteísmo (faltas no mês)
      const pastSessions = monthlyAppointments.filter(appt => {
        const d = new Date(appt.start_time);
        return d < now && appt.status !== "cancelled";
      });

      const missed = pastSessions.filter(appt => appt.status === "no_show" || appt.status === "missed");
      setMissedCount(missed.length);
      setTotalPastSessions(pastSessions.length);
      setAbsenteismoRate(pastSessions.length > 0 ? Math.round((missed.length / pastSessions.length) * 100) : 0);

      // C. Evoluções Pendentes de Assinatura (Consultas finalizadas sem evolução)
      // Uma consulta é considerada finalizada se ocorreu no passado e está confirmada/completed
      if (user?.role === "therapist" || user?.role === "admin") {
        const pastCompletedAppts = monthlyAppointments.filter(appt => {
          const d = new Date(appt.start_time);
          return d < now && (appt.status === "confirmed" || appt.status === "completed");
        });

        // Contamos quantas dessas consultas não têm correspondência de data e paciente nas evoluções
        let pending = 0;
        pastCompletedAppts.forEach(appt => {
          const apptDateStr = new Date(appt.start_time).toISOString().split("T")[0];
          
          // Verifica se existe alguma evolução cadastrada para o mesmo dia (ou próximo) do mesmo paciente
          const hasEv = evolutions.some(ev => {
            return ev.session_date === apptDateStr;
          });
          
          if (!hasEv) {
            pending++;
          }
        });
        setPendingEvolutionsCount(pending);
      } else {
        setPendingEvolutionsCount(0); // Secretária não gerencia prontuários
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
      scheduled: "bg-primary/10 text-primary border-primary/20",
      confirmed: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
      completed: "bg-slate-500/10 text-slate-500 border-slate-500/20",
      cancelled: "bg-destructive/10 text-destructive border-destructive/20",
      no_show: "bg-rose-500/10 text-rose-500 border-rose-500/20",
      missed: "bg-rose-500/10 text-rose-500 border-rose-500/20",
    };
    return classes[status as keyof typeof classes] || "bg-secondary text-muted-foreground";
  };

  return (
    <div className="space-y-6">
      {/* Cabeçalho de Boas-Vindas */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Olá, {user?.full_name?.split(" ")[0] || "Terapeuta"}
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Acompanhe o desempenho operacional e a conformidade da sua clínica.
          </p>
        </div>
        
        {/* Ações Rápidas de Topo */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => router.push("/dashboard/patients")}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Cadastrar Paciente
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-border/60 hover:bg-secondary/40"
            onClick={() => router.push("/dashboard/agenda")}
            leftIcon={<Calendar className="h-4 w-4" />}
          >
            Agendar Sessão
          </Button>
        </div>
      </div>

      {/* Grid de Cards de Indicadores Clínicos (KPIs) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* 1. Taxa de Ocupação Semanal */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Ocupação Semanal
              </span>
              <div className="h-8 w-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                <Percent className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : `${occupancyRate}%`}
              </h3>
              <div className="w-full bg-secondary rounded-full h-1.5 mt-2">
                <div 
                  className="bg-primary h-1.5 rounded-full transition-all duration-500" 
                  style={{ width: `${isLoadingData ? 0 : occupancyRate}%` }} 
                />
              </div>
              <p className="text-[10px] text-muted-foreground mt-2">
                {isLoadingData ? "Carregando..." : `${occupiedHours} de ${weeklyTarget} horas de grade ativa`}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 2. Evoluções Pendentes (Conformidade CFP) */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Evoluções Pendentes
              </span>
              <div className={cn(
                "h-8 w-8 rounded-md flex items-center justify-center",
                pendingEvolutionsCount > 0 ? "bg-amber-500/10 text-amber-500" : "bg-primary/10 text-primary"
              )}>
                <ClipboardCheck className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : pendingEvolutionsCount}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1.5">
                {pendingEvolutionsCount > 0 ? (
                  <>
                    <AlertCircle className="h-3 w-3 text-amber-500" />
                    <span className="text-amber-600 dark:text-amber-500 font-medium">Requer preenchimento</span>
                  </>
                ) : (
                  <>
                    <Check className="h-3 w-3 text-primary" />
                    <span>Conformidade CFP em dia</span>
                  </>
                )}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 3. Faturamento Faturado vs Recebido */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Faturamento Realizado
              </span>
              <div className="h-8 w-8 rounded-md bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                <DollarSign className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : `R$ ${faturamentoRecebido.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1.5">
                {isLoadingData ? "Carregando..." : `Líquido recebido de R$ ${faturamentoFaturado.toLocaleString("pt-BR")}`}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 4. Índice de Faltas/Abstenções */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Absenteísmo (Mês)
              </span>
              <div className={cn(
                "h-8 w-8 rounded-md flex items-center justify-center",
                absenteismoRate > 15 ? "bg-destructive/10 text-destructive" : "bg-secondary text-muted-foreground"
              )}>
                {absenteismoRate > 15 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : `${absenteismoRate}%`}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1.5">
                {absenteismoRate > 15 ? (
                  <>
                    <AlertTriangle className="h-3 w-3 text-destructive" />
                    <span className="text-destructive font-medium">Alerta de evasão clínica</span>
                  </>
                ) : (
                  <>
                    <Check className="h-3 w-3 text-primary" />
                    <span>{missedCount} faltas em {totalPastSessions} sessões</span>
                  </>
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Grid Principal - Agenda & Atalhos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Agenda do Dia */}
        <Card className="lg:col-span-2 border-border/80 bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-border/40">
            <div>
              <CardTitle className="text-base font-bold text-foreground">Agenda de Hoje</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Acompanhe e confirme a presença dos pacientes de hoje
              </CardDescription>
            </div>
            <span className="text-xs font-medium text-muted-foreground bg-secondary px-2.5 py-0.5 rounded-sm">
              {new Date().toLocaleDateString("pt-BR", { weekday: "short", day: "numeric", month: "short" })}
            </span>
          </CardHeader>
          
          <CardContent className="p-5">
            {isLoadingData ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <Activity className="h-6 w-6 text-primary animate-spin" />
                <span className="text-xs text-muted-foreground animate-pulse">Buscando consultas de hoje...</span>
              </div>
            ) : appointmentsToday.length === 0 ? (
              <div className="py-12 text-center flex flex-col items-center justify-center gap-3">
                <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground">
                  <Calendar className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-foreground">Nenhuma consulta hoje</h4>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xs mx-auto">
                    Sua agenda de hoje está livre de atendimentos registrados.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-2"
                  onClick={() => router.push("/dashboard/agenda")}
                >
                  Criar Agendamento
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {appointmentsToday.map((appt) => (
                  <div
                    key={appt.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-md border border-border/60 bg-card hover:bg-secondary/20 transition-all gap-3"
                  >
                    <div className="flex items-center gap-3">
                      {/* Horário da Consulta */}
                      <div className="flex flex-col items-center justify-center bg-secondary rounded-sm p-1.5 min-w-[64px] text-center border border-border/50">
                        <Clock className="h-3.5 w-3.5 text-muted-foreground mb-0.5" />
                        <span className="font-bold text-xs text-foreground">
                          {formatTime(appt.start_time)}
                        </span>
                      </div>

                      {/* Dados da Consulta */}
                      <div className="space-y-0.5">
                        <h4 className="font-semibold text-sm text-foreground">
                          {appt.patient_name}
                        </h4>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <span>Dr. {appt.therapist_name.split(" ")[0]}</span>
                          <span>•</span>
                          <span>Valor: R$ {parseFloat(appt.session_value).toFixed(0)}</span>
                          <span
                            className={cn(
                              "px-2 py-0.5 rounded-sm text-[9px] font-semibold border",
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
                            variant="secondary"
                            className="h-8 text-xs text-emerald-600 dark:text-emerald-500 cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "confirmed", "Confirmada")}
                            leftIcon={<Check className="h-3.5 w-3.5" />}
                          >
                            Confirmar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs text-destructive border-destructive/20 hover:bg-destructive/5 cursor-pointer"
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
                            variant="secondary"
                            className="h-8 text-xs text-foreground cursor-pointer"
                            onClick={() => handleUpdateStatus(appt.id, "completed", "Concluída")}
                            leftIcon={<UserCheck className="h-3.5 w-3.5" />}
                          >
                            Concluir
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 text-xs text-amber-600 dark:text-amber-500 border-amber-500/20 hover:bg-amber-500/5 cursor-pointer"
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
        <div className="space-y-4">
          {/* Ações Rápidas */}
          <Card className="border-border/80 bg-card shadow-xs">
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-sm font-bold text-foreground">Atalhos Clínicos</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">Navegação operacional rápida</CardDescription>
            </CardHeader>
            <CardContent className="p-3.5 space-y-1.5 mt-1.5">
              <button
                onClick={() => router.push("/dashboard/patients")}
                className="w-full flex items-center justify-between p-3 rounded-md border border-border/40 bg-card hover:bg-secondary/40 text-left transition-colors group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Users className="h-4.5 w-4.5 text-primary" />
                  <div className="text-xs font-semibold text-foreground">CRM de Pacientes</div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
              </button>

              {user && (user.role === "therapist" || user.role === "admin") && (
                <button
                  onClick={() => router.push("/dashboard/records")}
                  className="w-full flex items-center justify-between p-3 rounded-md border border-border/40 bg-card hover:bg-secondary/40 text-left transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <ClipboardCheck className="h-4.5 w-4.5 text-primary" />
                    <div className="text-xs font-semibold text-foreground">Prontuário Eletrônico</div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                </button>
              )}

              <button
                onClick={() => router.push("/dashboard/agenda")}
                className="w-full flex items-center justify-between p-3 rounded-md border border-border/40 bg-card hover:bg-secondary/40 text-left transition-colors group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-4.5 w-4.5 text-primary" />
                  <div className="text-xs font-semibold text-foreground">Calendário & Agenda</div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
              </button>

              <button
                onClick={() => router.push("/dashboard/financeiro")}
                className="w-full flex items-center justify-between p-3 rounded-md border border-border/40 bg-card hover:bg-secondary/40 text-left transition-colors group cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <DollarSign className="h-4.5 w-4.5 text-primary" />
                  <div className="text-xs font-semibold text-foreground">Painel Financeiro</div>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
              </button>
            </CardContent>
          </Card>

          {/* Dica de Segurança / Conformidade LGPD */}
          <Card className="bg-primary/5 border-primary/20 shadow-xs relative overflow-hidden">
            <div className="absolute top-0 left-0 h-full w-[3px] bg-primary" />
            <CardContent className="p-4 flex gap-3">
              <AlertCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <h5 className="font-semibold text-xs text-foreground">Segurança de Dados LGPD</h5>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  Prontuários e anamneses clínicas são criptografados de ponta a ponta na nuvem, atendendo à Resolução CFP nº 006/2019 e LGPD.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
