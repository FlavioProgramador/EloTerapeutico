"use client";

import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
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
import { Badge } from "@/components/ui/badge";
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import type { CreateTransactionPayload, TransactionType, TransactionStatus } from "@/types";

import { usePatients } from "@/features/patients/hooks/use-patients";
import {
  useTransactions,
  useFinancialSummary,
  useCreateTransaction,
  useMarkAsPaid,
  useDeleteTransaction,
} from "@/features/financeiro/hooks/use-financeiro";
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

  // Form com React Hook Form + Zod
  const todayStr = today.toISOString().split("T")[0];
  const {
    register,
    handleSubmit,
    watch,
    setValue,
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
      notes: "",
    },
  });

  const paymentStatusValue = watch("status");

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
      },
    });
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
            onClick={handleOpenModal}
            leftIcon={<Plus className="h-5 w-5" />}
            className="text-white font-semibold"
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
                  <Badge variant={tx.status === "paid" ? "success" : tx.status === "pending" ? "warning" : "muted"}>
                    {tx.status === "paid" ? "Pago" : tx.status === "pending" ? "Pendente" : tx.status === "overdue" ? "Atrasado" : "Cancelado"}
                  </Badge>
                </TableCell>

                {/* Ações */}
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    {tx.status === "pending" && (
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
