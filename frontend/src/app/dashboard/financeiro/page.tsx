"use client";

import React, { useEffect, useState } from "react";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Clock,
  Plus,
  Filter,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Trash2,
  Receipt,
  User,
  Search,
} from "lucide-react";
import { useToast } from "@/contexts/toast";
import { useAuth } from "@/contexts/auth";
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
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
  status: string;
}

interface FinancialTransaction {
  id: number;
  transaction_type: "income" | "expense";
  transaction_type_display: string;
  category: "session" | "subscription" | "material" | "refund" | "other";
  category_display: string;
  amount: string;
  payment_method: string;
  payment_method_display: string;
  payment_status: "paid" | "pending" | "cancelled";
  payment_status_display: string;
  patient_name: string | null;
  due_date: string | null;
  paid_at: string | null;
  created_at: string;
}

interface SummaryData {
  year: number;
  month: number;
  total_income: string;
  total_expense: string;
  balance: string;
  total_pending: string;
  transaction_count: number;
}

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
  const { user } = useAuth();
  const { toast } = useToast();

  const today = new Date();
  const [selectedYear, setSelectedYear] = useState(today.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1);

  // Dados principais
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [loadingTransactions, setLoadingTransactions] = useState(true);
  const [patients, setPatients] = useState<Patient[]>([]);

  // Filtros
  const [typeFilter, setTypeFilter] = useState<"all" | "income" | "expense">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "paid" | "pending" | "cancelled">("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [selectedPatientId, setSelectedPatientId] = useState<string>("all");

  // Modais
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const [selectedTxForPay, setSelectedTxForPay] = useState<number | null>(null);
  
  // Novo agendamento / Transação Manual form
  const [newTxForm, setNewTxForm] = useState({
    transaction_type: "expense", // Padrão despesa já que receita vem da agenda normalmente
    patient: "",
    category: "material",
    amount: "",
    payment_method: "pix",
    payment_status: "paid",
    due_date: new Date().toISOString().split("T")[0],
    paid_at: new Date().toISOString().split("T")[0],
    description: "",
  });

  // Confirmar recebimento form
  const [payForm, setPayForm] = useState({
    payment_method: "pix",
    paid_at: new Date().toISOString().split("T")[0] + "T" + new Date().toTimeString().split(" ")[0].slice(0, 5),
  });

  const [submittingTx, setSubmittingTx] = useState(false);
  const [submittingPay, setSubmittingPay] = useState(false);

  // Busca resumo financeiro
  const fetchSummary = async () => {
    setLoadingSummary(true);
    try {
      const response = await api.get<SummaryData>("financeiro/summary/", {
        params: {
          year: selectedYear,
          month: selectedMonth,
        },
      });
      setSummary(response.data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao buscar resumo",
        description: "Não foi possível carregar os cards de métricas financeiras.",
        variant: "destructive",
      });
    } finally {
      setLoadingSummary(false);
    }
  };

  // Busca lista de transações
  const fetchTransactions = async () => {
    setLoadingTransactions(true);
    try {
      const params: any = {};
      if (typeFilter !== "all") params.transaction_type = typeFilter;
      if (statusFilter !== "all") params.payment_status = statusFilter;
      if (categoryFilter !== "all") params.category = categoryFilter;
      if (selectedPatientId !== "all") params.patient = selectedPatientId;

      const response = await api.get("financeiro/", { params });
      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      setTransactions(data);
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao carregar transações",
        description: "Falha ao consultar a lista de histórico financeiro.",
        variant: "destructive",
      });
    } finally {
      setLoadingTransactions(false);
    }
  };

  // Busca pacientes
  const fetchPatients = async () => {
    try {
      const response = await api.get("patients/");
      const data = Array.isArray(response.data) ? response.data : (response.data as any).results || [];
      setPatients(data.filter((p: any) => p.status === "active"));
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [selectedYear, selectedMonth]);

  useEffect(() => {
    fetchTransactions();
  }, [typeFilter, statusFilter, categoryFilter, selectedPatientId]);

  useEffect(() => {
    fetchPatients();
  }, []);

  // Criar transação manual
  const handleCreateTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTxForm.amount || parseFloat(newTxForm.amount) <= 0) {
      toast({
        title: "Valor inválido",
        description: "O valor da transação deve ser maior que zero.",
        variant: "destructive",
      });
      return;
    }

    setSubmittingTx(true);
    try {
      const payload: any = {
        transaction_type: newTxForm.transaction_type,
        category: newTxForm.category,
        amount: newTxForm.amount,
        payment_method: newTxForm.payment_method,
        payment_status: newTxForm.payment_status,
        description: newTxForm.description,
      };

      if (newTxForm.patient) payload.patient = Number(newTxForm.patient);
      if (newTxForm.due_date) payload.due_date = newTxForm.due_date;
      
      if (newTxForm.payment_status === "paid") {
        payload.paid_at = newTxForm.paid_at ? new Date(newTxForm.paid_at).toISOString() : new Date().toISOString();
      }

      await api.post("financeiro/", payload);

      toast({
        title: "Transação registrada!",
        description: "O fluxo de caixa foi atualizado com sucesso.",
        variant: "success",
      });

      setIsNewModalOpen(false);
      // Reseta form
      setNewTxForm({
        transaction_type: "expense",
        patient: "",
        category: "material",
        amount: "",
        payment_method: "pix",
        payment_status: "paid",
        due_date: new Date().toISOString().split("T")[0],
        paid_at: new Date().toISOString().split("T")[0],
        description: "",
      });
      fetchSummary();
      fetchTransactions();
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao registrar transação",
        description: "Verifique os dados informados ou tente novamente mais tarde.",
        variant: "destructive",
      });
    } finally {
      setSubmittingTx(false);
    }
  };

  // Quitar transação pendente
  const handleMarkAsPaid = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTxForPay) return;

    setSubmittingPay(true);
    try {
      const payload = {
        payment_method: payForm.payment_method,
        paid_at: new Date(payForm.paid_at).toISOString(),
      };

      await api.patch(`financeiro/${selectedTxForPay}/pay/`, payload);

      toast({
        title: "Transação liquidada!",
        description: "O pagamento foi compensado no caixa da clínica.",
        variant: "success",
      });

      setIsPayModalOpen(false);
      setSelectedTxForPay(null);
      fetchSummary();
      fetchTransactions();
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao confirmar pagamento",
        description: "Não foi possível liquidar esta cobrança.",
        variant: "destructive",
      });
    } finally {
      setSubmittingPay(false);
    }
  };

  // Excluir transação
  const handleDeleteTransaction = async (id: number) => {
    if (!confirm("Deseja realmente excluir este registro de transação financeira?")) return;

    try {
      await api.delete(`financeiro/${id}/`);
      toast({
        title: "Transação excluída",
        description: "O registro foi removido do histórico.",
        variant: "success",
      });
      fetchSummary();
      fetchTransactions();
    } catch (error) {
      console.error(error);
      toast({
        title: "Erro ao excluir",
        description: "Esta transação não pôde ser excluída.",
        variant: "destructive",
      });
    }
  };

  // Alterar Mês
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

  return (
    <div className="space-y-8">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground/90 to-foreground/80">
            Fluxo Financeiro
          </h1>
          <p className="text-muted-foreground mt-1">
            Gestão de receitas de consultas, despesas clínicas e conciliação bancária
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Seletor de Período */}
          <div className="flex items-center border border-border/40 rounded-lg bg-card overflow-hidden">
            <button
              onClick={() => handleMonthChange("prev")}
              className="p-2 hover:bg-secondary/40 text-muted-foreground hover:text-foreground transition cursor-pointer"
            >
              <ChevronLeftIcon className="h-4.5 w-4.5" />
            </button>
            <div className="px-4 text-sm font-bold text-foreground select-none">
              {MONTHS[selectedMonth - 1]} / {selectedYear}
            </div>
            <button
              onClick={() => handleMonthChange("next")}
              className="p-2 hover:bg-secondary/40 text-muted-foreground hover:text-foreground transition cursor-pointer"
            >
              <ChevronRightIcon className="h-4.5 w-4.5" />
            </button>
          </div>

          <Button
            onClick={() => setIsNewModalOpen(true)}
            leftIcon={<Plus className="h-5 w-5" />}
            className="text-white font-semibold"
          >
            Lançar Transação
          </Button>
        </div>
      </div>

      {/* Cards de Resumos Analíticos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Receitas pagas */}
        <Card className="border-border/30 bg-card/65 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-emerald-500" />
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Faturamento (Pago)</p>
              <h3 className="text-2xl font-bold text-foreground font-mono">
                {loadingSummary ? "R$ ..." : `R$ ${parseFloat(summary?.total_income || "0.00").toFixed(2)}`}
              </h3>
            </div>
            <div className="h-10 w-10 bg-emerald-500/10 rounded-lg flex items-center justify-center text-emerald-500">
              <TrendingUp className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Despesas */}
        <Card className="border-border/30 bg-card/65 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-rose-500" />
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Despesas Totais</p>
              <h3 className="text-2xl font-bold text-foreground font-mono">
                {loadingSummary ? "R$ ..." : `R$ ${parseFloat(summary?.total_expense || "0.00").toFixed(2)}`}
              </h3>
            </div>
            <div className="h-10 w-10 bg-rose-500/10 rounded-lg flex items-center justify-center text-rose-500">
              <TrendingDown className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Saldo Líquido */}
        <Card className="border-border/30 bg-card/65 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-teal-500" />
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Saldo Líquido</p>
              <h3 className={`text-2xl font-bold font-mono ${
                summary && parseFloat(summary.balance) < 0 ? "text-rose-500" : "text-emerald-500"
              }`}>
                {loadingSummary ? "R$ ..." : `R$ ${parseFloat(summary?.balance || "0.00").toFixed(2)}`}
              </h3>
            </div>
            <div className="h-10 w-10 bg-teal-500/10 rounded-lg flex items-center justify-center text-teal-500">
              <DollarSign className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>

        {/* Pendentes */}
        <Card className="border-border/30 bg-card/65 backdrop-blur-md relative overflow-hidden">
          <div className="absolute top-0 left-0 h-full w-[4px] bg-amber-500" />
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">A Receber (Pendentes)</p>
              <h3 className="text-2xl font-bold text-foreground font-mono">
                {loadingSummary ? "R$ ..." : `R$ ${parseFloat(summary?.total_pending || "0.00").toFixed(2)}`}
              </h3>
            </div>
            <div className="h-10 w-10 bg-amber-500/10 rounded-lg flex items-center justify-center text-amber-500">
              <Clock className="h-5 w-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Barra de Filtros e Busca */}
      <Card className="border-border/30 bg-card/65 backdrop-blur-md p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Tipo de Transação */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase">Fluxo</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as any)}
              className="h-10 bg-secondary/35 border border-border/50 rounded-lg px-3 text-sm focus:outline-hidden focus:border-primary"
            >
              <option value="all">Todas as transações</option>
              <option value="income">Receita (Entradas)</option>
              <option value="expense">Despesa (Saídas)</option>
            </select>
          </div>

          {/* Status de Pagamento */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="h-10 bg-secondary/35 border border-border/50 rounded-lg px-3 text-sm focus:outline-hidden focus:border-primary"
            >
              <option value="all">Todos os Status</option>
              <option value="paid">Confirmados (Pagos)</option>
              <option value="pending">Abertos (Pendentes)</option>
              <option value="cancelled">Cancelados</option>
            </select>
          </div>

          {/* Categoria */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase">Categoria</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="h-10 bg-secondary/35 border border-border/50 rounded-lg px-3 text-sm focus:outline-hidden focus:border-primary"
            >
              <option value="all">Todas as Categorias</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          {/* Paciente */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-muted-foreground uppercase">Paciente</label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="h-10 bg-secondary/35 border border-border/50 rounded-lg px-3 text-sm focus:outline-hidden focus:border-primary"
            >
              <option value="all">Todos os Pacientes</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Histórico Financeiro */}
      {loadingTransactions ? (
        <div className="py-20 text-center flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground animate-pulse">Consultando fluxo de caixa...</span>
        </div>
      ) : transactions.length === 0 ? (
        <Card className="border-border/30 bg-card/65 backdrop-blur-md p-12 text-center flex flex-col items-center justify-center gap-4">
          <div className="h-12 w-12 rounded-full bg-secondary/50 flex items-center justify-center text-muted-foreground">
            <DollarSign className="h-6 w-6" />
          </div>
          <div>
            <h4 className="font-bold text-base text-foreground">Nenhuma movimentação no período</h4>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm">
              Não existem registros de receitas ou despesas com os filtros selecionados.
            </p>
          </div>
        </Card>
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
                <TableCell className="font-semibold text-foreground flex items-center gap-2">
                  {tx.transaction_type === "income" ? (
                    <div className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                      <ArrowUpRight className="h-4 w-4" />
                    </div>
                  ) : (
                    <div className="h-7 w-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-500">
                      <ArrowDownRight className="h-4 w-4" />
                    </div>
                  )}
                  <span>{tx.transaction_type_display}</span>
                </TableCell>
                
                {/* Paciente */}
                <TableCell className="text-slate-300 font-medium">
                  {tx.patient_name || <span className="text-muted-foreground/60 italic">Não associado</span>}
                </TableCell>

                {/* Categoria */}
                <TableCell className="text-muted-foreground text-xs">{tx.category_display}</TableCell>

                {/* Valor */}
                <TableCell className={`font-bold font-mono ${
                  tx.transaction_type === "income" ? "text-emerald-500" : "text-rose-500"
                }`}>
                  {tx.transaction_type === "income" ? "+" : "-"} R$ {parseFloat(tx.amount).toFixed(2)}
                </TableCell>

                {/* Data de Vencimento ou Pagamento */}
                <TableCell className="text-muted-foreground text-xs">
                  {tx.payment_status === "paid" && tx.paid_at ? (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-emerald-500" />
                      {new Date(tx.paid_at).toLocaleDateString("pt-BR")}
                    </span>
                  ) : tx.due_date ? (
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-amber-500" />
                      {new Date(tx.due_date).toLocaleDateString("pt-BR")}
                    </span>
                  ) : (
                    "---"
                  )}
                </TableCell>

                {/* Status */}
                <TableCell>
                  <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold border capitalize ${
                    tx.payment_status === "paid"
                      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                      : tx.payment_status === "pending"
                      ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                      : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                  }`}>
                    {tx.payment_status_display}
                  </span>
                </TableCell>

                {/* Ações */}
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    {tx.payment_status === "pending" && (
                      <Button
                        size="sm"
                        variant="glass"
                        onClick={() => {
                          setSelectedTxForPay(tx.id);
                          setIsPayModalOpen(true);
                        }}
                        leftIcon={<CheckCircle className="h-3.5 w-3.5" />}
                        className="text-xs hover:bg-emerald-500/10 border-emerald-500/20 text-emerald-500 cursor-pointer"
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
        <form onSubmit={handleCreateTransaction} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Tipo */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Tipo de Fluxo *</label>
              <select
                value={newTxForm.transaction_type}
                onChange={(e) => setNewTxForm({ ...newTxForm, transaction_type: e.target.value })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="expense">Despesa (Saída de caixa)</option>
                <option value="income">Receita (Entrada de caixa)</option>
              </select>
            </div>

            {/* Categoria */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Categoria *</label>
              <select
                value={newTxForm.category}
                onChange={(e) => setNewTxForm({ ...newTxForm, category: e.target.value })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Valor */}
            <Input
              label="Valor da Transação (R$) *"
              type="number"
              step="0.01"
              value={newTxForm.amount}
              onChange={(e) => setNewTxForm({ ...newTxForm, amount: e.target.value })}
              required
              leftIcon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
              className="bg-secondary/20"
            />

            {/* Paciente (Opcional) */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground flex items-center gap-1">
                <User className="h-4 w-4" /> Paciente (Opcional)
              </label>
              <select
                value={newTxForm.patient}
                onChange={(e) => setNewTxForm({ ...newTxForm, patient: e.target.value })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="">Nenhum associado...</option>
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>{p.full_name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Status */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Status do Pagamento *</label>
              <select
                value={newTxForm.payment_status}
                onChange={(e) => setNewTxForm({ ...newTxForm, payment_status: e.target.value })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                <option value="paid">Compensado (Pago)</option>
                <option value="pending">Aberto (Pendente)</option>
              </select>
            </div>

            {/* Método de pagamento */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-semibold text-muted-foreground">Forma de Pagamento</label>
              <select
                value={newTxForm.payment_method}
                onChange={(e) => setNewTxForm({ ...newTxForm, payment_method: e.target.value })}
                className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
              >
                {PAYMENT_METHODS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Data de Vencimento */}
            <Input
              label="Data de Vencimento"
              type="date"
              value={newTxForm.due_date}
              onChange={(e) => setNewTxForm({ ...newTxForm, due_date: e.target.value })}
              className="bg-secondary/20"
            />

            {/* Data de Pagamento */}
            {newTxForm.payment_status === "paid" && (
              <Input
                label="Data do Pagamento"
                type="date"
                value={newTxForm.paid_at}
                onChange={(e) => setNewTxForm({ ...newTxForm, paid_at: e.target.value })}
                className="bg-secondary/20"
              />
            )}
          </div>

          {/* Descrição */}
          <Textarea
            label="Descrição / Detalhes"
            placeholder="Descreva detalhes do lançamento (ex: Compra de materiais de escritório)..."
            value={newTxForm.description}
            onChange={(e) => setNewTxForm({ ...newTxForm, description: e.target.value })}
            className="bg-secondary/20 min-h-[80px]"
          />

          {/* Ações */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsNewModalOpen(false)}
              className="border-border text-foreground px-5"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={submittingTx}
              className="text-white font-semibold px-5"
            >
              Salvar Lançamento
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: COMPENSAR PAGAMENTO (PENDENTE -> PAGO) */}
      <Modal
        isOpen={isPayModalOpen}
        onClose={() => {
          setIsPayModalOpen(false);
          setSelectedTxForPay(null);
        }}
        title="Quitar Lançamento"
        description="Confirme o recebimento/pagamento desta cobrança no caixa."
        className="max-w-md"
      >
        <form onSubmit={handleMarkAsPaid} className="space-y-4">
          {/* Método de pagamento */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-muted-foreground">Forma de Recebimento *</label>
            <select
              value={payForm.payment_method}
              onChange={(e) => setPayForm({ ...payForm, payment_method: e.target.value })}
              className="w-full h-11 bg-secondary/20 border border-border rounded-lg px-3.5 text-base focus:outline-hidden focus:border-primary"
            >
              {PAYMENT_METHODS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Data do pagamento */}
          <Input
            label="Data/Hora da Compensação *"
            type="datetime-local"
            value={payForm.paid_at}
            onChange={(e) => setPayForm({ ...payForm, paid_at: e.target.value })}
            required
            className="bg-secondary/20"
          />

          {/* Ações */}
          <div className="flex gap-3 justify-end pt-4 border-t border-border/40">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsPayModalOpen(false);
                setSelectedTxForPay(null);
              }}
              className="border-border text-foreground"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={submittingPay}
              className="text-white font-semibold"
            >
              Confirmar Recebimento
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

// Icones auxiliares
function ChevronLeftIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

function ChevronRightIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="m9 18 6-6-6-6" />
    </svg>
  );
}
