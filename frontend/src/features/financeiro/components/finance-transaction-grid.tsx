import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { FinancialTransaction } from "@/types";
import { formatDate, formatMoney, parseMoney, PAYMENT_METHODS, STATUS_LABEL, transactionStatusClass } from "./financeiro-shared";

export function FinanceTransactionGrid({ transactions, hidden, renderActions }: { transactions: FinancialTransaction[]; hidden: boolean; renderActions: (transaction: FinancialTransaction) => ReactNode }) {
  return (
    <div className="overflow-x-auto p-4">
      <table className="w-full min-w-[920px] border-separate border-spacing-0 text-sm">
        <thead><tr className="text-left text-xs uppercase tracking-wide text-muted-foreground"><th className="rounded-l-xl border-y border-l border-border px-4 py-3">Paciente</th><th className="border-y border-border px-4 py-3">Descrição</th><th className="border-y border-border px-4 py-3">Valor</th><th className="border-y border-border px-4 py-3">Vencimento</th><th className="border-y border-border px-4 py-3">Data pgto.</th><th className="border-y border-border px-4 py-3">Meio de pgto.</th><th className="border-y border-border px-4 py-3">Status</th><th className="rounded-r-xl border-y border-r border-border px-4 py-3 text-right">Ações</th></tr></thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td className="border-b border-border px-4 py-4 font-medium text-foreground">{transaction.patient_name || "—"}</td>
              <td className="max-w-72 border-b border-border px-4 py-4 text-foreground"><span className="line-clamp-2">{transaction.description || transaction.category_display || "Lançamento financeiro"}</span></td>
              <td className="border-b border-border px-4 py-4 font-semibold text-foreground">{formatMoney(parseMoney(transaction.amount), hidden)}</td>
              <td className="border-b border-border px-4 py-4">{formatDate(transaction.due_date)}</td>
              <td className="border-b border-border px-4 py-4">{formatDate(transaction.payment_date)}</td>
              <td className="border-b border-border px-4 py-4">{PAYMENT_METHODS.find((method) => method.value === transaction.payment_method)?.label || "—"}</td>
              <td className="border-b border-border px-4 py-4"><span className={cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-medium", transactionStatusClass(transaction.status))}>{STATUS_LABEL[transaction.status]}</span></td>
              <td className="relative border-b border-border px-4 py-4 text-right">{renderActions(transaction)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
