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
  Bell,
  Search,
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
    const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1);
    startOfWeek.setDate(diff);
    startOfWeek.setHours(0, 0, 0, 0);

    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    endOfWeek.setHours(23, 59, 59, 999);

    const weeklyAppts = monthlyAppointments.filter(appt => {
      const d = new Date(appt.start_time);
      return d >= startOfWeek && d <= endOfWeek && appt.status !== "cancelled";
    });

    const occupiedHours = weeklyAppts.length;
    const weeklyTarget = 30;
    const occupancyRate = Math.min(Math.round((occupiedHours / weeklyTarget) * 100), 100);

    // B. Receita Mensal
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
      faturamentoFaturado,
      faturamentoRecebido,
    };
  }, [monthlyAppointments, transactions, now, month, year]);

  const isLoadingData = loadingToday || loadingPatients || loadingMonthly || loadingEvolutions || loadingFinance;

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

  return (
    <div className="space-y-6 text-left">
      {/* Cabeçalho de Boas-Vindas */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[hsl(40,20%,94%)] font-sans">
            Visão geral
          </h1>
          <p className="text-xs text-[hsl(163,8%,68%)] mt-0.5">
            Bem-vinda de volta, {user?.full_name || "Juliana Martins"} 🍂
          </p>
        </div>
        
        {/* Ações Rápidas de Topo */}
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => router.push("/dashboard/patients")}
            className="bg-[hsl(38,25%,87%)] hover:bg-[hsl(38,22%,83%)] text-[hsl(165,40%,7%)] font-bold rounded-lg px-4 py-2 flex items-center gap-1.5 transition-all text-xs"
          >
            <Plus className="h-4 w-4" /> Cadastrar Paciente
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-[hsl(165,27%,16%)] hover:bg-[hsl(165,27%,12%)] text-[hsl(40,20%,94%)] rounded-lg px-4 py-2 flex items-center gap-1.5 transition-all text-xs"
            onClick={() => router.push("/dashboard/agenda")}
          >
            <Calendar className="h-4 w-4" /> Agendar Sessão
          </Button>
        </div>
      </div>

      {/* Grid de Cards de Indicadores (Métricas) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* 1. Atendimentos */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-32 relative overflow-hidden">
            <div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[hsl(163,8%,68%)] uppercase tracking-wider">
                  Atendimentos
                </span>
                <div className="h-7 w-7 rounded-lg bg-[hsl(163,27%,62%)]/10 flex items-center justify-center text-[hsl(163,27%,62%)]">
                  <Calendar className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-3xl font-bold tracking-tight text-[hsl(40,20%,94%)] mt-2">
                23
              </h3>
            </div>
            <div className="flex items-center justify-between mt-2 z-10">
              <span className="text-[9px] text-[hsl(163,27%,62%)] font-semibold flex items-center gap-1">
                ↑ 12% <span className="text-[hsl(163,8%,68%)]">vs semana passada</span>
              </span>
              {/* Mini Sparkline SVG */}
              <svg className="w-16 h-6 text-[hsl(163,27%,62%)]" viewBox="0 0 100 30" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M0 25 Q15 5 30 18 T60 8 T90 20 T100 5" />
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* 2. Novos Pacientes */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-32 relative overflow-hidden">
            <div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[hsl(163,8%,68%)] uppercase tracking-wider">
                  Novos pacientes
                </span>
                <div className="h-7 w-7 rounded-lg bg-[hsl(163,27%,62%)]/10 flex items-center justify-center text-[hsl(163,27%,62%)]">
                  <Users className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-3xl font-bold tracking-tight text-[hsl(40,20%,94%)] mt-2">
                4
              </h3>
            </div>
            <div className="flex items-center justify-between mt-2 z-10">
              <span className="text-[9px] text-[hsl(163,27%,62%)] font-semibold flex items-center gap-1">
                ↑ 8% <span className="text-[hsl(163,8%,68%)]">vs semana passada</span>
              </span>
              {/* Mini Sparkline SVG */}
              <svg className="w-16 h-6 text-[hsl(163,27%,62%)]" viewBox="0 0 100 30" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M0 20 Q20 25 40 10 T70 15 T100 5" />
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* 3. Receita */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-32 relative overflow-hidden">
            <div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[hsl(163,8%,68%)] uppercase tracking-wider">
                  Receita
                </span>
                <div className="h-7 w-7 rounded-lg bg-[hsl(163,27%,62%)]/10 flex items-center justify-center text-[hsl(163,27%,62%)]">
                  <DollarSign className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-xl md:text-2xl font-bold tracking-tight text-[hsl(40,20%,94%)] mt-2">
                R$ 8.540,00
              </h3>
            </div>
            <div className="flex items-center justify-between mt-2 z-10">
              <span className="text-[9px] text-[hsl(163,27%,62%)] font-semibold flex items-center gap-1">
                ↑ 15% <span className="text-[hsl(163,8%,68%)]">vs semana passada</span>
              </span>
              {/* Mini Sparkline SVG */}
              <svg className="w-16 h-6 text-[hsl(163,27%,62%)]" viewBox="0 0 100 30" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M0 25 Q15 15 30 5 T60 12 T90 2 T100 8" />
              </svg>
            </div>
          </CardContent>
        </Card>

        {/* 4. Taxa de ocupação */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardContent className="p-5 flex flex-col justify-between h-32 relative overflow-hidden">
            <div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[hsl(163,8%,68%)] uppercase tracking-wider">
                  Taxa de ocupação
                </span>
                <div className="h-7 w-7 rounded-lg bg-[hsl(163,27%,62%)]/10 flex items-center justify-center text-[hsl(163,27%,62%)]">
                  <Percent className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-3xl font-bold tracking-tight text-[hsl(40,20%,94%)] mt-2">
                82%
              </h3>
            </div>
            <div className="flex items-center justify-between mt-2 z-10">
              <span className="text-[9px] text-[hsl(163,27%,62%)] font-semibold flex items-center gap-1">
                ↑ 4% <span className="text-[hsl(163,8%,68%)]">vs semana passada</span>
              </span>
              {/* Mini Sparkline SVG */}
              <svg className="w-16 h-6 text-[hsl(163,27%,62%)]" viewBox="0 0 100 30" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M0 15 Q20 5 45 20 T80 8 T100 12" />
              </svg>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Grid Principal - Agenda, Financeiro e Atividades (3 Colunas conforme Imagem) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Agenda de hoje */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardHeader className="pb-3 border-b border-[hsl(165,27%,16%)]/40 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-[hsl(40,20%,94%)]">Agenda de hoje</CardTitle>
              <CardDescription className="text-[10px] text-[hsl(163,8%,68%)]">
                23 de maio, sexta-feira
              </CardDescription>
            </div>
            <Button variant="ghost" className="text-xs text-[hsl(163,27%,62%)] p-0 hover:bg-transparent">
              Ver agenda completa ▾
            </Button>
          </CardHeader>
          
          <CardContent className="p-5">
            {loadingToday ? (
              <div className="py-12 flex flex-col items-center justify-center gap-2">
                <Activity className="h-6 w-6 text-[hsl(163,27%,62%)] animate-spin" />
                <span className="text-xs text-[hsl(163,8%,68%)]">Buscando consultas de hoje...</span>
              </div>
            ) : appointmentsToday.length === 0 ? (
              <div className="py-12 text-center flex flex-col items-center justify-center gap-3">
                <Calendar className="h-8 w-8 text-[hsl(163,8%,68%)] opacity-40" />
                <div>
                  <h4 className="font-semibold text-xs text-[hsl(40,20%,94%)]">Nenhuma consulta agendada</h4>
                  <p className="text-[10px] text-[hsl(163,8%,68%)] mt-1 max-w-xs mx-auto">
                    Sua agenda de hoje está livre de atendimentos registrados.
                  </p>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-[hsl(165,27%,16%)]/40">
                {appointmentsToday.map((appt) => (
                  <div
                    key={appt.id}
                    className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0"
                  >
                    <div className="flex items-center gap-4">
                      {/* Horário */}
                      <div className="text-center min-w-[50px]">
                        <span className="font-bold text-xs text-[hsl(40,20%,94%)]">
                          {formatTime(appt.start_time)}
                        </span>
                        <span className="block text-[8px] text-[hsl(163,8%,68%)]">
                          {formatTime(appt.end_time)}
                        </span>
                      </div>

                      {/* Detalhes */}
                      <div>
                        <h4 className="font-bold text-xs text-[hsl(40,20%,94%)]">
                          {appt.patient_name}
                        </h4>
                        <span className="text-[9px] text-[hsl(163,8%,68%)]">
                          Terapia individual
                        </span>
                      </div>
                    </div>

                    {/* Badge Status */}
                    <div className="flex items-center gap-3">
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-[9px] font-bold border",
                        appt.status === "confirmed" || appt.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      )}>
                        {appt.status === "confirmed" || appt.status === "completed" ? "Confirmada" : "Pendente"}
                      </span>
                      
                      {/* Ações rápidas */}
                      {appt.status === "scheduled" && (
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleUpdateStatus(appt.id, "confirmed", "Confirmada")}
                            className="h-6 w-6 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 flex items-center justify-center cursor-pointer"
                            title="Confirmar Presença"
                          >
                            <Check className="h-3 w-3" />
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(appt.id, "cancelled", "Cancelada")}
                            className="h-6 w-6 rounded bg-destructive/20 hover:bg-destructive/30 text-destructive flex items-center justify-center cursor-pointer"
                            title="Cancelar Consulta"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resumo financeiro */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] shadow-sm">
          <CardHeader className="pb-3 border-b border-[hsl(165,27%,16%)]/40">
            <CardTitle className="text-sm font-bold text-[hsl(40,20%,94%)]">Resumo financeiro</CardTitle>
            <CardDescription className="text-[10px] text-[hsl(163,8%,68%)]">Este mês</CardDescription>
          </CardHeader>
          <CardContent className="p-5 space-y-6">
            
            {/* Barra de Receitas e Despesas */}
            <div className="space-y-4">
              {/* Receitas */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[hsl(163,8%,68%)]">Receitas</span>
                  <span className="font-bold text-[hsl(40,20%,94%)]">R$ 12.450,00</span>
                </div>
                <div className="w-full bg-[hsl(165,27%,12%)] rounded-full h-1.5">
                  <div className="bg-emerald-400 h-1.5 rounded-full" style={{ width: "75%" }} />
                </div>
                <span className="block text-[9px] text-[hsl(163,8%,68%)] text-right">75% do esperado</span>
              </div>

              {/* Despesas */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-[hsl(163,8%,68%)]">Despesas</span>
                  <span className="font-bold text-[hsl(40,20%,94%)]">R$ 3.210,00</span>
                </div>
                <div className="w-full bg-[hsl(165,27%,12%)] rounded-full h-1.5">
                  <div className="bg-red-400 h-1.5 rounded-full" style={{ width: "25%" }} />
                </div>
                <span className="block text-[9px] text-[hsl(163,8%,68%)] text-right">25% das receitas</span>
              </div>
            </div>

            {/* Lucro Líquido e Sparkline Principal */}
            <div className="pt-4 border-t border-[hsl(165,27%,16%)]/40 flex flex-col items-start gap-4">
              <div>
                <span className="text-[10px] text-[hsl(163,8%,68%)] uppercase tracking-wider block">Lucro líquido</span>
                <span className="text-xl font-bold text-[hsl(40,20%,94%)]">R$ 9.240,00</span>
              </div>

              {/* Gráfico SVG Grande */}
              <div className="w-full h-20 relative">
                <svg className="w-full h-full text-[hsl(163,27%,62%)]" viewBox="0 0 300 60" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="currentColor" stopOpacity="0.2" />
                      <stop offset="100%" stopColor="currentColor" stopOpacity="0.0" />
                    </linearGradient>
                  </defs>
                  <path d="M0 50 C30 40 60 55 90 35 C120 15 150 45 180 20 C210 -5 240 18 270 5 L300 25" stroke="currentColor" strokeWidth="2.5" />
                  <path d="M0 50 C30 40 60 55 90 35 C120 15 150 45 180 20 C210 -5 240 18 270 5 L300 25 V60 H0 Z" fill="url(#netGrad)" />
                </svg>
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[8px] text-[hsl(163,8%,68%)]/60 px-1 font-mono pt-1.5">
                  <span>1 Mai</span>
                  <span>8 Mai</span>
                  <span>15 Mai</span>
                  <span>22 Mai</span>
                  <span>29 Mai</span>
                </div>
              </div>
            </div>

          </CardContent>
        </Card>

        {/* Atividades recentes */}
        <Card className="border-[hsl(165,27%,16%)] bg-[hsl(165,38%,10%)] h-full shadow-sm">
          <CardHeader className="pb-3 border-b border-[hsl(165,27%,16%)]/40 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm font-bold text-[hsl(40,20%,94%)]">Atividades recentes</CardTitle>
              <CardDescription className="text-[10px] text-[hsl(163,8%,68%)]">Movimentações da clínica</CardDescription>
            </div>
          </CardHeader>
          
          <CardContent className="p-5">
            <div className="relative border-l border-[hsl(165,27%,16%)]/80 ml-3.5 pl-5 space-y-6 py-2">
              
              {/* Atividade 1 */}
              <div className="relative">
                {/* Círculo */}
                <div className="absolute -left-[29px] top-0.5 h-4.5 w-4.5 rounded-full bg-[hsl(165,27%,12%)] border-2 border-[hsl(163,27%,62%)] flex items-center justify-center text-[hsl(163,27%,62%)]">
                  <Users className="h-2 w-2" />
                </div>
                <div className="space-y-0.5">
                  <h5 className="font-bold text-xs text-[hsl(40,20%,94%)]">Novo paciente cadastrado</h5>
                  <p className="text-[10px] text-[hsl(163,8%,68%)]">Ana Clara Sousa</p>
                  <span className="block text-[8px] text-[hsl(163,8%,68%)]/50 pt-0.5">Há 20 min</span>
                </div>
              </div>

              {/* Atividade 2 */}
              <div className="relative">
                {/* Círculo */}
                <div className="absolute -left-[29px] top-0.5 h-4.5 w-4.5 rounded-full bg-[hsl(165,27%,12%)] border-2 border-emerald-400 flex items-center justify-center text-emerald-400">
                  <DollarSign className="h-2 w-2" />
                </div>
                <div className="space-y-0.5">
                  <h5 className="font-bold text-xs text-[hsl(40,20%,94%)]">Pagamento recebido</h5>
                  <p className="text-[10px] text-[hsl(163,8%,68%)]">R$ 250,00 de Marcos Lima</p>
                  <span className="block text-[8px] text-[hsl(163,8%,68%)]/50 pt-0.5">Há 2h</span>
                </div>
              </div>

              {/* Atividade 3 */}
              <div className="relative">
                {/* Círculo */}
                <div className="absolute -left-[29px] top-0.5 h-4.5 w-4.5 rounded-full bg-[hsl(165,27%,12%)] border-2 border-amber-400 flex items-center justify-center text-amber-400">
                  <ClipboardCheck className="h-2 w-2" />
                </div>
                <div className="space-y-0.5">
                  <h5 className="font-bold text-xs text-[hsl(40,20%,94%)]">Prontuário atualizado</h5>
                  <p className="text-[10px] text-[hsl(163,8%,68%)]">Juliana Rocha</p>
                  <span className="block text-[8px] text-[hsl(163,8%,68%)]/50 pt-0.5">Há 3h</span>
                </div>
              </div>

              {/* Atividade 4 */}
              <div className="relative">
                {/* Círculo */}
                <div className="absolute -left-[29px] top-0.5 h-4.5 w-4.5 rounded-full bg-[hsl(165,27%,12%)] border-2 border-[hsl(38,25%,87%)] flex items-center justify-center text-[hsl(38,25%,87%)]">
                  <Check className="h-2 w-2" />
                </div>
                <div className="space-y-0.5">
                  <h5 className="font-bold text-xs text-[hsl(40,20%,94%)]">Nova mensagem</h5>
                  <p className="text-[10px] text-[hsl(163,8%,68%)]">De: Ana Clara Sousa</p>
                  <span className="block text-[8px] text-[hsl(163,8%,68%)]/50 pt-0.5">Há 5h</span>
                </div>
              </div>

            </div>

            <Button variant="ghost" className="w-full text-xs text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] pt-4 border-t border-[hsl(165,27%,16%)]/40 mt-4 justify-between hover:bg-transparent">
              Ver todas atividades <ChevronRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
