"use client";

import React, { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Clock,
  Plus,
  Filter,
  CheckCircle,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Trash2,
  Receipt,
  User,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";

import { Card } from "@/components/ui/card";
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
import { Badge, getTransactionStatusVariant } from "@/components/ui/badge";
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import type { CreateTransactionPayload, TransactionType } from "@/types";
import { usePatients } from "@/features/patients/hooks/use-patients";

import {
  useTransactions,
  useFinancialSummary,
  useCreateTransaction,
  useMarkAsPaid,
  useDeleteTransaction,
  useCancelTransaction,
  useRefundTransaction,
  useUnbilledAppointments,
} from "@/features/financeiro/hooks/use-financeiro";
import { financeiroService } from "@/features/financeiro/services/financeiro.service";
import { transactionSchema, type TransactionFormData } from "@/features/financeiro/schemas/transaction.schemas";

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const CATEGORIES = [
  { value: "session", label: "Sessão Terapêutica" },
  { value: "subscription", label: "Assinatura / Plano" },
  { value: "material", label: "Material Clínico" },
  { value: "refund", label: "Reembolso" },
  { value: "other", label: "Outro" },
];

const PAYMENT_METHODS = [
  { value: "pix", label: "PIX" },
  { value: "credit_card", label: "Cartão de Crédito" },
  { value: "debit_card", label: "Cartão de Débito" },
  { value: "cash", label: "Dinheiro" },
  { value: "bank_transfer", label: "Transferência Bancária" },
  { value: "other", label: "Outro" },
];

export default function FinanceiroPage() {
  const today = new Date();
  const [selectedYear, setSelectedYear] = useState(today.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1);

  // Filtros de listagem
  const [typeFilter, setTypeFilter] = useState<"all" | "income" | "expense">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "paid" | "pending" | "cancelled">("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedPatientId, setSelectedPatientId] = useState<string>("all");

  const [isNewModalOpen, setIsNewModalOpen] = useState(false);

  // TanStack Query
  const { data: patientsData } = usePatients({ status: "active" });
  const activePatients = patientsData?.results || [];

  const {
    data: summary,
    isLoading: loadingSummary,
    refetch: refetchSummary,
  } = useFinancialSummary(selectedYear, selectedMonth);

  const {
    data: transactions = [],
    isLoading: loadingTransactions,
    refetch: refetchTransactions,
  } = useTransactions({
    transaction_type: typeFilter === "all" ? undefined : typeFilter,
    payment_status: statusFilter === "all" ? undefined : statusFilter,
    category: categoryFilter === "all" ? undefined : categoryFilter,
    patient: selectedPatientId === "all" ? undefined : selectedPatientId,
  });

  const createTxMutation = useCreateTransaction();
  const markAsPaidMutation = useMarkAsPaid();
  const deleteTxMutation = useDeleteTransaction();
  const cancelTxMutation = useCancelTransaction();
  const refundTxMutation = useRefundTransaction();
  const { data: unbilledAppts = [], refetch: refetchUnbilled } = useUnbilledAppointments();

  // Form com React Hook Form + Zod
  const todayStr = today.toISOString().split("T")[0];
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema),
    defaultValues: {
      type: "expense",
      category: "material",
      amount: "",
      payment_method: "pix",
      status: "paid",
      due_date: todayStr,
      payment_date: todayStr,
      description: "",
      patient: undefined,
      appointment: undefined,
      notes: "",
    },
  });

  const paymentStatusValue = useWatch({ control, name: "status" });

  // Ajusta valores quando abre o modal
  const handleOpenModal = () => {
    reset({
      type: "expense",
      category: "material",
      amount: "",
      payment_method: "pix",
      status: "paid",
      due_date: todayStr,
      payment_date: todayStr,
      description: "",
      patient: undefined,
      appointment: undefined,
      notes: "",
    });
    setIsNewModalOpen(true);
  };

  // Trata submissão da transação
  const onSubmit = async (data: TransactionFormData) => {
    const payload = {
      ...data,
      amount: parseFloat(data.amount.replace(",", ".")),
      patient: data.patient ? Number(data.patient) : undefined,
      appointment: data.appointment ? Number(data.appointment) : undefined,
      payment_date: data.status === "paid" ? data.payment_date : undefined,
      payment_method: data.payment_method || undefined,
    };

    createTxMutation.mutate(payload as CreateTransactionPayload, {
      onSuccess: () => {
        setIsNewModalOpen(false);
        refetchSummary();
        refetchTransactions();
        refetchUnbilled();
      },
    });
  };

  // Quitar transação com 1 clique
  const handleQuickPay = async (txId: number) => {
    markAsPaidMutation.mutate(
      { id: txId, paymentMethod: "pix" },
      {
        onSuccess: () => {
          refetchSummary();
          refetchTransactions();
          refetchUnbilled();
        },
      }
    );
  };

  // Excluir transação
  const handleDeleteTransaction = async (id: number) => {
    if (!confirm("Deseja realmente excluir este registro de transação financeira?")) return;
    deleteTxMutation.mutate(id, {
      onSuccess: () => {
        refetchSummary();
        refetchTransactions();
        refetchUnbilled();
      },
    });
  };

  // Cancelar transação com confirmação
  const handleCancelTransaction = async (id: number) => {
    if (!confirm("Tem certeza que deseja cancelar esta transação pendente?")) return;
    cancelTxMutation.mutate(id, {
      onSuccess: () => {
        refetchSummary();
        refetchTransactions();
        refetchUnbilled();
      },
    });
  };

  // Estornar transação com confirmação
  const handleRefundTransaction = async (id: number) => {
    if (!confirm("Tem certeza que deseja estornar esta transação paga? O valor será marcado como estornado no fluxo.")) return;
    refundTxMutation.mutate(id, {
      onSuccess: () => {
        refetchSummary();
        refetchTransactions();
        refetchUnbilled();
      },
    });
  };

  // Trata exportação de CSV
  const handleExportCSV = async () => {
    try {
      const filters = {
        transaction_type: typeFilter === "all" ? undefined : typeFilter,
        payment_status: statusFilter === "all" ? undefined : statusFilter,
        category: categoryFilter === "all" ? undefined : categoryFilter,
        patient: selectedPatientId === "all" ? undefined : selectedPatientId,
      };
      
      const blob = await financeiroService.exportCSV(filters);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `fluxo-financeiro-${selectedYear}-${selectedMonth}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success("Relatório financeiro CSV exportado com sucesso!");
    } catch (error) {
      console.error(error);
      toast.error("Erro ao exportar relatório financeiro. Tente novamente.");
    }
  };

  // Faturamento rápido de consulta concluída
  const handleQuickBill = (appt: {
    id: number;
    patient_id: number;
    patient_name: string;
    start_time: string;
    session_value: string;
  }) => {
    const apptDate = appt.start_time.split("T")[0];
    reset({
      type: "income",
      category: "session",
      amount: parseFloat(appt.session_value).toFixed(2).replace(".", ","),
      payment_method: "pix",
      status: "pending",
      due_date: apptDate,
      payment_date: apptDate,
      description: `Faturamento automático de consulta em ${new Date(appt.start_time).toLocaleDateString("pt-BR")}`,
      patient: String(appt.patient_id),
      appointment: String(appt.id),
      notes: "",
    });
    setIsNewModalOpen(true);
  };

  // Navegar meses
  const handleMonthChange = (direction: "prev" | "next") => {
    if (direction === "prev") {
      if (selectedMonth === 1) {
        setSelectedMonth(12);
        setSelectedYear(selectedYear - 1);
      } else {
        setSelectedMonth(selectedMonth - 1);
      }
    } else {
      if (selectedMonth === 12) {
        setSelectedMonth(1);
        setSelectedYear(selectedYear + 1);
      } else {
        setSelectedMonth(selectedMonth + 1);
      }
    }
  };

  const getCategoryLabel = (cat: string) => {
    return CATEGORIES.find((c) => c.value === cat)?.label || cat;
  };

  // Agrupa dados para os gráficos CSS dinâmicos
  const categorySummary = React.useMemo(() => {
    const categoriesMap: Record<string, { income: number; expense: number }> = {};
    
    CATEGORIES.forEach(c => {
      categoriesMap[c.value] = { income: 0, expense: 0 };
    });
    
    let maxAmount = 0;
    
    transactions.forEach(tx => {
      const amount = parseFloat(tx.amount);
      const cat = tx.category || "other";
      if (!categoriesMap[cat]) {
        categoriesMap[cat] = { income: 0, expense: 0 };
      }
      if (tx.type === "income") {
        categoriesMap[cat].income += amount;
      } else {
        categoriesMap[cat].expense += amount;
      }
    });

    const list = Object.entries(categoriesMap).map(([key, val]) => {
      const label = getCategoryLabel(key);
      const total = val.income + val.expense;
      if (total > maxAmount) maxAmount = total;
      return {
        key,
        label,
        income: val.income,
        expense: val.expense,
        total,
      };
    }).filter(item => item.total > 0)
      .sort((a, b) => b.total - a.total);

    return { list, maxAmount };
  }, [transactions]);

  const totalVolume = parseFloat(summary?.total_income || "0") + parseFloat(summary?.total_expense || "0");

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
            Fluxo Financeiro
          </h1>
          <p className="text-muted-foreground mt-1">
            Gestão de receitas de consultas, despesas clínicas e conciliação bancária
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Seletor de Período */}
          <div className="flex items-center border border-border/60 rounded-md bg-card overflow-hidden h-11">
            <button
              onClick={() => handleMonthChange("prev")}
              className="p-3 hover:bg-secondary text-muted-foreground hover:text-foreground transition cursor-pointer"
            >
              <ChevronLeft className="h-4.5 w-4.5" />
            </button>
            <div className="px-4 text-sm font-semibold text-foreground select-none">
              {MONTHS[selectedMonth - 1]} / {selectedYear}
            </div>
            <button
              onClick={() => handleMonthChange("next")}
              className="p-3 hover:bg-secondary text-muted-foreground hover:text-foreground transition cursor-pointer"
            >
              <ChevronRight className="h-4.5 w-4.5" />
            </button>
          </div>

          <Button
            onClick={handleExportCSV}
            variant="outline"
            leftIcon={<Receipt className="h-5 w-5" />}
            className="text-foreground border border-border hover:bg-secondary shrink-0 font-semibold cursor-pointer h-11"
          >
            Exportar CSV
          </Button>

          <Button
            onClick={handleOpenModal}
            leftIcon={<Plus className="h-5 w-5" />}
            className="text-white font-semibold cursor-pointer h-11"
          >
            Lançar Transação
          </Button>
        </div>
      </div>

      {/* Cards de Resumos Analíticos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loadingSummary ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            {/* Receitas pagas */}
            <Card className="border-border/80 bg-card shadow-xs">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Faturamento (Pago)
                  </span>
                  <div className="h-8 w-8 rounded-md bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <TrendingUp className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <h3 className="text-2xl font-bold tracking-tight text-foreground font-mono">
                    R$ {parseFloat(summary?.total_income || "0.00").toFixed(2)}
                  </h3>
                  <p className="text-[10px] text-muted-foreground mt-2">
                    Receitas compensadas no período
                  </p>
                </div>
              </div>
            </Card>

            {/* Despesas */}
            <Card className="border-border/80 bg-card shadow-xs">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Despesas Totais
                  </span>
                  <div className="h-8 w-8 rounded-md bg-rose-500/10 flex items-center justify-center text-rose-600 dark:text-rose-400">
                    <TrendingDown className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <h3 className="text-2xl font-bold tracking-tight text-foreground font-mono">
                    R$ {parseFloat(summary?.total_expense || "0.00").toFixed(2)}
                  </h3>
                  <p className="text-[10px] text-muted-foreground mt-2">
                    Total de saídas operacionais
                  </p>
                </div>
              </div>
            </Card>

            {/* Saldo Líquido */}
            <Card className="border-border/80 bg-card shadow-xs">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Saldo Líquido
                  </span>
                  <div className={cn(
                    "h-8 w-8 rounded-md flex items-center justify-center",
                    summary && parseFloat(summary.balance) < 0 ? "bg-rose-500/10 text-rose-600 dark:text-rose-400" : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                  )}>
                    <DollarSign className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <h3 className={cn(
                    "text-2xl font-bold tracking-tight font-mono",
                    summary && parseFloat(summary.balance) < 0 ? "text-rose-600 dark:text-rose-400" : "text-emerald-600 dark:text-emerald-400"
                  )}>
                    R$ {parseFloat(summary?.balance || "0.00").toFixed(2)}
                  </h3>
                  <p className="text-[10px] text-muted-foreground mt-2">
                    Resultado financeiro consolidado
                  </p>
                </div>
              </div>
            </Card>

            {/* Pendentes */}
            <Card className="border-border/80 bg-card shadow-xs">
              <div className="p-5">
                <div className="flex justify-between items-start">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    A Receber (Pendentes)
                  </span>
                  <div className="h-8 w-8 rounded-md bg-amber-500/10 flex items-center justify-center text-amber-500">
                    <Clock className="h-4 w-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <h3 className="text-2xl font-bold tracking-tight text-foreground font-mono">
                    R$ {parseFloat(summary?.total_pending || "0.00").toFixed(2)}
                  </h3>
                  <p className="text-[10px] text-muted-foreground mt-2">
                    Valores aguardando liquidação
                  </p>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>

      {/* Gráficos Analíticos Premium */}
      {!loadingSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Comparativo do Mês */}
          <Card className="border-border/80 bg-card shadow-xs p-5 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Saúde Financeira do Período
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                Visualização de proporção entre Entradas (Receitas) e Saídas (Despesas) pagas
              </p>
            </div>
            
            <div className="flex items-end justify-around h-44 mt-6 border-b border-border/40 pb-2">
              {/* Barra de Receitas */}
              <div className="flex flex-col items-center gap-2 w-16">
                <span className="text-[10px] font-bold font-mono text-emerald-600 dark:text-emerald-400">
                  R$ {parseFloat(summary?.total_income || "0").toFixed(0)}
                </span>
                <div 
                  style={{ height: `${totalVolume > 0 ? (parseFloat(summary?.total_income || "0") / Math.max(parseFloat(summary?.total_income || "0"), parseFloat(summary?.total_expense || "0"), 1)) * 130 : 10}px` }}
                  className="w-full bg-gradient-to-t from-emerald-500/80 to-emerald-400/80 rounded-t-md hover:from-emerald-500 hover:to-emerald-400 transition-all duration-500 shrink-0 cursor-pointer shadow-md shadow-emerald-500/10"
                  title={`Receitas: R$ ${parseFloat(summary?.total_income || "0").toFixed(2)}`}
                />
                <span className="text-xs font-semibold text-foreground">Receitas</span>
              </div>

              {/* Barra de Despesas */}
              <div className="flex flex-col items-center gap-2 w-16">
                <span className="text-[10px] font-bold font-mono text-rose-600 dark:text-rose-400">
                  R$ {parseFloat(summary?.total_expense || "0").toFixed(0)}
                </span>
                <div 
                  style={{ height: `${totalVolume > 0 ? (parseFloat(summary?.total_expense || "0") / Math.max(parseFloat(summary?.total_income || "0"), parseFloat(summary?.total_expense || "0"), 1)) * 130 : 10}px` }}
                  className="w-full bg-gradient-to-t from-rose-500/80 to-rose-400/80 rounded-t-md hover:from-rose-500 hover:to-rose-400 transition-all duration-500 shrink-0 cursor-pointer shadow-md shadow-rose-500/10"
                  title={`Despesas: R$ ${parseFloat(summary?.total_expense || "0").toFixed(2)}`}
                />
                <span className="text-xs font-semibold text-foreground">Despesas</span>
              </div>
            </div>

            <div className="mt-4 flex justify-between text-xs text-muted-foreground border-t border-border/20 pt-4">
              <span>Aproveitamento Financeiro:</span>
              <span className="font-semibold text-foreground">
                {parseFloat(summary?.total_income || "0") > 0 
                  ? `${((parseFloat(summary?.balance || "0") / parseFloat(summary?.total_income || "0")) * 100).toFixed(0)}% de margem`
                  : "0% de margem"
                }
              </span>
            </div>
          </Card>

          {/* Card 2: Distribuição por Categorias */}
          <Card className="border-border/80 bg-card shadow-xs p-5">
            <div>
              <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                Distribuição por Categoria
              </h3>
              <p className="text-xs text-muted-foreground mt-1">
                Volume financeiro proporcional a cada categoria (Entradas + Saídas)
              </p>
            </div>

            <div className="mt-6 space-y-4 max-h-[178px] overflow-y-auto pr-1">
              {categorySummary.list.length === 0 ? (
                <div className="h-40 flex items-center justify-center text-xs text-muted-foreground/60 italic">
                  Sem movimentação no período para gráficos
                </div>
              ) : (
                categorySummary.list.map(item => (
                  <div key={item.key} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-foreground">{item.label}</span>
                      <span className="font-mono text-muted-foreground font-semibold">
                        R$ {item.total.toFixed(2)}
                      </span>
                    </div>
                    <div className="h-3 w-full bg-secondary/40 rounded-full overflow-hidden flex border border-border/10">
                      {item.income > 0 && (
                        <div 
                          style={{ width: `${(item.income / categorySummary.maxAmount) * 100}%` }}
                          className="h-full bg-emerald-500/80 hover:bg-emerald-500 transition-all duration-300 relative"
                          title={`Receitas de ${item.label}: R$ ${item.income.toFixed(2)}`}
                        />
                      )}
                      {item.expense > 0 && (
                        <div 
                          style={{ width: `${(item.expense / categorySummary.maxAmount) * 100}%` }}
                          className="h-full bg-rose-500/80 hover:bg-rose-500 transition-all duration-300 relative"
                          title={`Despesas de ${item.label}: R$ ${item.expense.toFixed(2)}`}
                        />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Alerta de Consultas Pendentes de Faturamento */}
      {unbilledAppts.length > 0 && (
        <Card className="border-amber-500/20 bg-amber-500/5 shadow-xs p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 rounded-md bg-amber-500/10 flex items-center justify-center text-amber-600 shrink-0">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <h4 className="font-semibold text-sm text-foreground">
                Você tem {unbilledAppts.length} {unbilledAppts.length === 1 ? "consulta confirmada" : "consultas confirmadas"} pendente de faturamento
              </h4>
              <p className="text-xs text-muted-foreground mt-0.5">
                Lance estas sessões no fluxo financeiro para manter o controle de recebimentos e a cobrança de seus pacientes em dia.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 shrink-0 max-w-full">
            {unbilledAppts.slice(0, 3).map((appt) => (
              <Button
                key={appt.id}
                size="sm"
                variant="outline"
                onClick={() => handleQuickBill(appt)}
                leftIcon={<Plus className="h-3.5 w-3.5" />}
                className="text-xs hover:bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400 font-medium whitespace-nowrap cursor-pointer h-9"
              >
                Faturar {appt.patient_name.split(" ")[0]} (R$ {parseFloat(appt.session_value).toFixed(0)})
              </Button>
            ))}
            {unbilledAppts.length > 3 && (
              <span className="text-[10px] text-muted-foreground font-semibold px-2">
                +{unbilledAppts.length - 3} mais
              </span>
            )}
          </div>
        </Card>
      )}

      {/* Barra de Filtros Compacta */}
      <Card className="border-border/80 bg-card shadow-xs p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Filtrar por:</span>
          </div>

          {/* Tipo de Transação */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as "all" | TransactionType)}
            className="h-9 bg-card border border-border/60 rounded-md px-3 text-xs focus:outline-none focus:border-primary focus:ring-1 focus:ring-ring text-foreground cursor-pointer"
          >
            <option value="all">Todos os Fluxos</option>
            <option value="income">Receita (Entradas)</option>
            <option value="expense">Despesa (Saídas)</option>
          </select>

          {/* Status de Pagamento */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as "all" | "paid" | "pending" | "cancelled")}
            className="h-9 bg-card border border-border/60 rounded-md px-3 text-xs focus:outline-none focus:border-primary focus:ring-1 focus:ring-ring text-foreground cursor-pointer"
          >
            <option value="all">Todos os Status</option>
            <option value="paid">Confirmados (Pagos)</option>
            <option value="pending">Abertos (Pendentes)</option>
            <option value="cancelled">Cancelados</option>
          </select>

          {/* Categoria */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="h-9 bg-card border border-border/60 rounded-md px-3 text-xs focus:outline-none focus:border-primary focus:ring-1 focus:ring-ring text-foreground cursor-pointer"
          >
            <option value="all">Todas as Categorias</option>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>

          {/* Paciente */}
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="h-9 bg-card border border-border/60 rounded-md px-3 text-xs focus:outline-none focus:border-primary focus:ring-1 focus:ring-ring text-foreground cursor-pointer max-w-xs"
          >
            <option value="all">Todos os Pacientes</option>
            {activePatients.map((p) => (
              <option key={p.id} value={String(p.id)}>{p.full_name}</option>
            ))}
          </select>
        </div>
      </Card>

      {/* Histórico Financeiro */}
      {loadingTransactions ? (
        <SkeletonTable rows={5} />
      ) : transactions.length === 0 ? (
        <EmptyState
          title="Nenhuma movimentação no período"
          description="Não existem registros de receitas ou despesas com os filtros selecionados."
          icon={<DollarSign className="h-6 w-6 text-muted-foreground" />}
        />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Lançamento</TableHead>
              <TableHead>Paciente</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead>Valor</TableHead>
              <TableHead>Vencimento / Pago em</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => (
              <TableRow key={tx.id}>
                {/* Tipo e Indicador */}
                <TableCell className="font-semibold text-foreground">
                  <div className="flex items-center gap-2">
                    {tx.type === "income" ? (
                      <div className="h-7 w-7 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
                        <ArrowUpRight className="h-4 w-4" />
                      </div>
                    ) : (
                      <div className="h-7 w-7 rounded-md bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
                        <ArrowDownRight className="h-4 w-4" />
                      </div>
                    )}
                    <span>{tx.type === "income" ? "Receita" : "Despesa"}</span>
                  </div>
                </TableCell>
                
                {/* Paciente */}
                <TableCell className="font-medium text-foreground">
                  {tx.patient_name || <span className="text-muted-foreground/60 italic font-normal text-xs">Não associado</span>}
                </TableCell>

                {/* Categoria */}
                <TableCell className="text-muted-foreground text-xs">{getCategoryLabel(tx.category)}</TableCell>

                {/* Valor */}
                <TableCell className={cn(
                  "font-bold font-mono text-sm tracking-tight",
                  tx.type === "income" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                )}>
                  {tx.type === "income" ? "+" : "-"} R$ {parseFloat(tx.amount).toFixed(2)}
                </TableCell>

                {/* Data de Vencimento ou Pagamento */}
                <TableCell className="text-muted-foreground text-xs">
                  {tx.status === "paid" && tx.payment_date ? (
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                      {new Date(tx.payment_date + "T12:00:00").toLocaleDateString("pt-BR")}
                    </span>
                  ) : tx.due_date ? (
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-amber-500" />
                      {new Date(tx.due_date + "T12:00:00").toLocaleDateString("pt-BR")}
                    </span>
                  ) : (
                    "---"
                  )}
                </TableCell>

                {/* Status */}
                <TableCell>
                  <Badge variant={getTransactionStatusVariant(tx.status)}>
                    {tx.status === "paid" ? "Pago" : tx.status === "pending" ? "Pendente" : tx.status === "overdue" ? "Atrasado" : tx.status === "refunded" ? "Estornado" : "Cancelado"}
                  </Badge>
                </TableCell>

                {/* Ações */}
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {(tx.status === "pending" || tx.status === "overdue") && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleQuickPay(tx.id)}
                          isLoading={markAsPaidMutation.isPending}
                          leftIcon={<CheckCircle className="h-3.5 w-3.5" />}
                          className="text-xs hover:bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400 cursor-pointer h-8"
                        >
                          Compensar
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleCancelTransaction(tx.id)}
                          isLoading={cancelTxMutation.isPending}
                          className="text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/5 cursor-pointer h-8"
                        >
                          Cancelar
                        </Button>
                      </>
                    )}
                    {tx.status === "paid" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRefundTransaction(tx.id)}
                        isLoading={refundTxMutation.isPending}
                        className="text-xs text-amber-600 dark:text-amber-500 hover:bg-amber-500/10 cursor-pointer h-8"
                      >
                        Estornar
                      </Button>
                    )}
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => alert("Geração de recibo em desenvolvimento.")}
                      className="h-8 w-8 text-muted-foreground hover:text-foreground cursor-pointer"
                      title="Emitir Recibo"
                    >
                      <Receipt className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => handleDeleteTransaction(tx.id)}
                      className="h-8 w-8 text-destructive/80 hover:text-destructive hover:bg-destructive/5 cursor-pointer"
                      title="Excluir Transação"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* MODAL: LANÇAR TRANSAÇÃO MANUAL */}
      <Modal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        title="Lançar Transação Financeira"
        description="Lance despesas operacionais da clínica ou receitas manuais avulsas."
        className="max-w-xl"
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Tipo */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="tx-type" className="text-sm font-semibold text-muted-foreground">Tipo de Fluxo *</label>
              <select
                id="tx-type"
                {...register("type")}
                className="w-full h-11 bg-card border border-border rounded-md px-3.5 text-base focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-ring transition-colors text-foreground cursor-pointer"
              >
                <option value="expense">Despesa (Saída de caixa)</option>
                <option value="income">Receita (Entrada de caixa)</option>
              </select>
            </div>

            {/* Categoria */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="tx-category" className="text-sm font-semibold text-muted-foreground">Categoria *</label>
              <select
                id="tx-category"
                {...register("category")}
                className="w-full h-11 bg-card border border-border rounded-md px-3.5 text-base focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-ring transition-colors text-foreground cursor-pointer"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Valor */}
            <div className="space-y-1">
              <Input
                id="tx-amount"
                label="Valor da Transação (R$) *"
                type="text"
                placeholder="0.00"
                aria-invalid={!!errors.amount}
                error={errors.amount?.message}
                leftIcon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
                className="bg-card"
                {...register("amount")}
              />
            </div>

            {/* Paciente (Opcional) */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="tx-patient" className="text-sm font-semibold text-muted-foreground flex items-center gap-1">
                <User className="h-4 w-4 text-muted-foreground" /> Paciente (Opcional)
              </label>
              <select
                id="tx-patient"
                {...register("patient")}
                className="w-full h-11 bg-card border border-border rounded-md px-3.5 text-base focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-ring transition-colors text-foreground cursor-pointer"
              >
                <option value="">Nenhum associado...</option>
                {activePatients.map((p) => (
                  <option key={p.id} value={p.id}>{p.full_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Status */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="tx-status" className="text-sm font-semibold text-muted-foreground">Status do Pagamento *</label>
              <select
                id="tx-status"
                {...register("status")}
                className="w-full h-11 bg-card border border-border rounded-md px-3.5 text-base focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-ring transition-colors text-foreground cursor-pointer"
              >
                <option value="paid">Compensado (Pago)</option>
                <option value="pending">Aberto (Pendente)</option>
              </select>
            </div>

            {/* Método de pagamento */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="tx-method" className="text-sm font-semibold text-muted-foreground">Forma de Pagamento</label>
              <select
                id="tx-method"
                {...register("payment_method")}
                className="w-full h-11 bg-card border border-border rounded-md px-3.5 text-base focus:outline-hidden focus:border-primary focus:ring-1 focus:ring-ring transition-colors text-foreground cursor-pointer"
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Data de Vencimento */}
            <div className="space-y-1">
              <Input
                id="tx-duedate"
                label="Data de Vencimento *"
                type="date"
                aria-invalid={!!errors.due_date}
                error={errors.due_date?.message}
                className="bg-card"
                {...register("due_date")}
              />
            </div>

            {/* Data de Pagamento */}
            {paymentStatusValue === "paid" && (
              <div className="space-y-1">
                <Input
                  id="tx-paydate"
                  label="Data do Pagamento *"
                  type="date"
                  aria-invalid={!!errors.payment_date}
                  error={errors.payment_date?.message}
                  className="bg-card"
                  {...register("payment_date")}
                />
              </div>
            )}
          </div>

          {/* Descrição */}
          <div className="space-y-1">
            <Textarea
              id="tx-desc"
              label="Descrição / Detalhes *"
              placeholder="Descreva detalhes do lançamento (ex: Compra de materiais de escritório)..."
              aria-invalid={!!errors.description}
              error={errors.description?.message}
              className="bg-card min-h-[80px]"
              {...register("description")}
            />
          </div>

          {/* Ações */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsNewModalOpen(false)}
              className="border-border text-foreground px-5 h-11"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              className="text-white font-semibold px-5 h-11"
            >
              Salvar Lançamento
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
