import { CheckCircle2, Plus, ReceiptText, XCircle } from "lucide-react";

import { Badge, getTransactionStatusVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonTable } from "@/components/ui/skeleton";
import type { FinancialTransaction } from "@/types";

import { formatCurrency, formatDate, TRANSACTION_STATUS_LABELS, PAYMENT_METHOD_LABELS } from "../financeiro-formatters";
import { FinanceiroActionsMenu } from "./financeiro-actions-menu";

interface Props {
  mode: "income" | "expense";
  transactions: FinancialTransaction[];
  isLoading: boolean;
  hidden: boolean;
  onCreate: () => void;
  onMarkPaid: (id: number) => void;
  onCancel: (id: number) => void;
  onEdit?: (id: number) => void;
  onDelete?: (id: number) => void;
  onRefund?: (id: number) => void;
  onGenerateCharges?: () => void;
  onNewCharge?: () => void;
  actionPending?: boolean;
}

export function FinanceiroTransactionsPanel({
  mode,
  transactions,
  isLoading,
  hidden,
  onCreate,
  onMarkPaid,
  onCancel,
  onEdit,
  onDelete,
  onRefund,
  onGenerateCharges,
  onNewCharge,
  actionPending,
}: Props) {
  const isIncome = mode === "income";
  const title = isIncome ? "Contas a receber" : "Contas a pagar";
  const description = isIncome ? "Cobranças pendentes de pacientes" : "Despesas e contas pendentes";

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-border p-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-lg font-bold">{title}</h2>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {isIncome && onGenerateCharges && (
            <Button variant="outline" size="sm" onClick={onGenerateCharges} leftIcon={<ReceiptText className="h-4 w-4" />}>
              Gerar cobranças do mês
            </Button>
          )}
          {isIncome && onNewCharge && (
            <Button variant="outline" size="sm" onClick={onNewCharge} leftIcon={<Plus className="h-4 w-4" />}>
              Nova cobrança
            </Button>
          )}
          <Button size="sm" onClick={onCreate} leftIcon={<Plus className="h-4 w-4" />}>
            {isIncome ? "Nova receita" : "Nova despesa"}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="p-5"><SkeletonTable /></div>
      ) : transactions.length === 0 ? (
        <EmptyState
          icon={<ReceiptText className="h-5 w-5 text-muted-foreground" />}
          title={isIncome ? "Nenhuma conta a receber cadastrada" : "Nenhuma conta a pagar cadastrada"}
          description="Os lançamentos compatíveis com os filtros selecionados aparecerão aqui."
          action={<Button size="sm" onClick={onCreate}>Criar lançamento</Button>}
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] text-left text-sm">
            <thead className="border-b border-border bg-secondary/30 text-xs uppercase text-muted-foreground">
              <tr>
                {isIncome && <th className="px-5 py-3">Paciente</th>}
                <th className="px-5 py-3">Descrição</th>
                <th className="px-5 py-3">Valor</th>
                <th className="px-5 py-3">Vencimento</th>
                <th className="px-5 py-3">Data pgto.</th>
                <th className="px-5 py-3">Meio Pgto.</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3 text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id} className="border-b border-border/60 last:border-0 hover:bg-secondary/20">
                  {isIncome && <td className="px-5 py-4 font-semibold">{transaction.patient_name ?? "—"}</td>}
                  <td className="max-w-72 truncate px-5 py-4">{transaction.description || "Sem descrição"}</td>
                  <td className="px-5 py-4 font-semibold">{formatCurrency(transaction.amount, hidden)}</td>
                  <td className="px-5 py-4">{formatDate(transaction.due_date)}</td>
                  <td className="px-5 py-4">{formatDate(transaction.payment_date)}</td>
                  <td className="px-5 py-4 text-xs font-medium text-muted-foreground">{transaction.payment_method ? PAYMENT_METHOD_LABELS[transaction.payment_method] : "—"}</td>
                  <td className="px-5 py-4">
                    <Badge variant={getTransactionStatusVariant(transaction.status)}>
                      {TRANSACTION_STATUS_LABELS[transaction.status] ?? transaction.status}
                    </Badge>
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex justify-end gap-1">
                      <FinanceiroActionsMenu 
                        transaction={transaction}
                        onEdit={onEdit}
                        onMarkPaid={onMarkPaid}
                        onCancel={onCancel}
                        onDelete={onDelete}
                        onRefund={onRefund}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="border-t border-border px-5 py-3 text-xs text-muted-foreground">
        {transactions.length} registro{transactions.length === 1 ? "" : "s"}
      </div>
    </Card>
  );
}
