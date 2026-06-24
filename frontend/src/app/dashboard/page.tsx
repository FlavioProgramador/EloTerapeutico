"use client";

import React, { useMemo } from "react";
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
import { toast } from "sonner";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { usePatients } from "@/features/patients/hooks/use-patients";
import { useTodayAppointments, useAppointments, useUpdateAppointmentStatus } from "@/features/agenda/hooks/use-agenda";
import { useRecords } from "@/features/records/hooks/use-records";
import { useTransactions } from "@/features/financeiro/hooks/use-financeiro";

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  const now = useMemo(() => new Date(), []);
  const year = now.getFullYear();
  const month = now.getMonth();
  const startOfMonth = useMemo(() => new Date(year, month, 1).toISOString(), [year, month]);
  const endOfMonth = useMemo(() => new Date(year, month + 1, 0, 23, 59, 59).toISOString(), [year, month]);

  // TanStack Query
  const { data: appointmentsToday = [], isLoading: loadingToday, refetch: refetchToday } = useTodayAppointments();
  const { data: patientsData, isLoading: loadingPatients } = usePatients();
  const { data: monthlyAppointments = [], isLoading: loadingMonthly } = useAppointments({
    start_time_gte: startOfMonth,
    start_time_lte: endOfMonth,
  });
  const { data: evolutions = [], isLoading: loadingEvolutions } = useRecords();
  const { data: transactions = [], isLoading: loadingFinance } = useTransactions();

  const updateStatusMutation = useUpdateAppointmentStatus();

  const patientCount = patientsData?.results?.length || 0;

  // Cálculos dos KPIs Clínicos e Financeiros
  const kpis = useMemo(() => {
    // A. Ocupação Semanal
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

    const occupiedHours = weeklyAppts.length;
    const weeklyTarget = 30; // Grade padrão
    const occupancyRate = Math.min(Math.round((occupiedHours / weeklyTarget) * 100), 100);

    // B. Absenteísmo (faltas no mês)
    const pastSessions = monthlyAppointments.filter(appt => {
      const d = new Date(appt.start_time);
      return d < now && appt.status !== "cancelled";
    });
    const missedCount = pastSessions.filter(appt => appt.status === "missed").length;
    const totalPastSessions = pastSessions.length;
    const absenteismoRate = totalPastSessions > 0 ? Math.round((missedCount / totalPastSessions) * 100) : 0;

    // C. Evoluções Pendentes de Assinatura (para Terapeutas/Admins)
    let pendingEvolutionsCount = 0;
    if (user?.role === "therapist" || user?.role === "admin") {
      const pastCompletedAppts = monthlyAppointments.filter(appt => {
        const d = new Date(appt.start_time);
        return d < now && (appt.status === "confirmed" || appt.status === "completed");
      });

      pastCompletedAppts.forEach(appt => {
        const apptDateStr = new Date(appt.start_time).toISOString().split("T")[0];
        const hasEv = evolutions.some(ev => ev.session_date === apptDateStr);
        if (!hasEv) {
          pendingEvolutionsCount++;
        }
      });
    }

    // D. Faturamento Faturado vs Recebido
    let faturamentoFaturado = 0;
    let faturamentoRecebido = 0;

    transactions.forEach((tx) => {
      const amount = parseFloat(tx.amount || "0");
      const txDate = new Date(tx.due_date || tx.created_at);
      if (txDate.getMonth() === month && txDate.getFullYear() === year) {
        if (tx.type === "income") {
          faturamentoFaturado += amount;
          if (tx.status === "paid") {
            faturamentoRecebido += amount;
          }
        }
      }
    });

    return {
      occupancyRate,
      occupiedHours,
      weeklyTarget,
      pendingEvolutionsCount,
      faturamentoFaturado,
      faturamentoRecebido,
      absenteismoRate,
      missedCount,
      totalPastSessions,
    };
  }, [monthlyAppointments, transactions, evolutions, user, now, month, year]);

  const isLoadingData = loadingToday || loadingPatients || loadingMonthly || loadingEvolutions || loadingFinance;

  // Alteração de status da consulta de hoje
  const handleUpdateStatus = (appointmentId: number, newStatus: string, statusLabel: string) => {
    updateStatusMutation.mutate(
      { id: appointmentId, status: newStatus },
      {
        onSuccess: () => {
          refetchToday();
        },
      }
    );
  };

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return "--:--";
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    const variants: Record<string, "default" | "primary" | "success" | "warning" | "destructive" | "outline" | "muted"> = {
      scheduled: "primary",
      confirmed: "success",
      completed: "muted",
      cancelled: "destructive",
      missed: "warning",
    };
    return variants[status] || "default";
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
            className="border-border/60 hover:bg-secondary/40 text-foreground"
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
                {isLoadingData ? "..." : `${kpis.occupancyRate}%`}
              </h3>
              <div className="w-full bg-secondary rounded-full h-1.5 mt-2">
                <div 
                  className="bg-primary h-1.5 rounded-full transition-all duration-500" 
                  style={{ width: `${isLoadingData ? 0 : kpis.occupancyRate}%` }} 
                />
              </div>
              <p className="text-[10px] text-muted-foreground mt-2">
                {isLoadingData ? "Carregando..." : `${kpis.occupiedHours} de ${kpis.weeklyTarget} horas de grade ativa`}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* 2. Evoluções Pendentes */}
        <Card className="border-border/80 bg-card shadow-xs">
          <CardContent className="p-5">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Evoluções Pendentes
              </span>
              <div className={cn(
                "h-8 w-8 rounded-md flex items-center justify-center",
                kpis.pendingEvolutionsCount > 0 ? "bg-amber-500/10 text-amber-500" : "bg-primary/10 text-primary"
              )}>
                <ClipboardCheck className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : kpis.pendingEvolutionsCount}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1.5">
                {kpis.pendingEvolutionsCount > 0 ? (
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
                {isLoadingData ? "..." : `R$ ${kpis.faturamentoRecebido.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1.5">
                {isLoadingData ? "Carregando..." : `Líquido recebido de R$ ${kpis.faturamentoFaturado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`}
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
                kpis.absenteismoRate > 15 ? "bg-destructive/10 text-destructive" : "bg-secondary text-muted-foreground"
              )}>
                {kpis.absenteismoRate > 15 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
              </div>
            </div>
            <div className="mt-3">
              <h3 className="text-2xl font-bold tracking-tight text-foreground">
                {isLoadingData ? "..." : `${kpis.absenteismoRate}%`}
              </h3>
              <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1.5">
                {kpis.absenteismoRate > 15 ? (
                  <>
                    <AlertTriangle className="h-3 w-3 text-destructive" />
                    <span className="text-destructive font-medium">Alerta de evasão clínica</span>
                  </>
                ) : (
                  <>
                    <Check className="h-3 w-3 text-primary" />
                    <span>{kpis.missedCount} faltas em {kpis.totalPastSessions} sessões</span>
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
            {loadingToday ? (
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
                  className="mt-2 text-foreground border-border hover:bg-secondary/60"
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
                          <span>Dr. {appt.therapist_name?.split(" ")[0]}</span>
                          <span>•</span>
                          <span>Valor: R$ {parseFloat(appt.session_value || "0").toFixed(0)}</span>
                          <Badge variant={getStatusBadgeVariant(appt.status)}>
                            {appt.status_display}
                          </Badge>
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
                            className="h-8 text-xs text-emerald-600 dark:text-emerald-500 cursor-pointer border border-emerald-500/10 hover:bg-emerald-500/5"
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
                            onClick={() => handleUpdateStatus(appt.id, "missed", "Falta Registrada")}
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
                        onClick={() => router.push(`/dashboard/patients/${appt.patient || appt.id}`)}
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
