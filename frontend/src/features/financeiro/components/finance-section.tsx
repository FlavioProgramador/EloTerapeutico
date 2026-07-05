import type { ReactNode } from "react";
import { CalendarDays, Plus, ReceiptText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonTable } from "@/components/ui/skeleton";
import type { FinancialTransaction, TransactionStatus } from "@/types";
import { FinanceFilters } from "./finance-filters";
import { FinanceTabs } from "./finance-tabs";
import { FinanceTransactionGrid } from "./finance-transaction-grid";
import type { FinanceTab } from "./financeiro-shared";

export function FinanceSection({ tab, setTab, transactions, patients, loading, hidden, status, setStatus, patient, setPatient, search, setSearch, actions, renderRowActions, onRefresh, onCreate }: { tab: FinanceTab; setTab: (tab: FinanceTab) => void; transactions: FinancialTransaction[]; patients: Array<{ id: number; full_name: string }>; loading: boolean; hidden: boolean; status: "all" | TransactionStatus; setStatus: (status: "all" | TransactionStatus) => void; patient: string; setPatient: (patient: string) => void; search: string; setSearch: (value: string) => void; actions: ReactNode; renderRowActions: (transaction: FinancialTransaction) => ReactNode; onRefresh: () => void; onCreate: () => void }) {
  return (
    <>
      <FinanceTabs tab={tab} onChange={setTab} />
      <Card className="overflow-visible border-border bg-card">
        <div className="flex flex-col gap-4 border-b border-border p-5 xl:flex-row xl:items-center xl:justify-between">
          <div><h2 className="font-semibold text-foreground">{title(tab)}</h2><p className="mt-1 text-sm text-muted-foreground">{subtitle(tab)}</p></div>
          <div className="flex flex-wrap gap-2">{actions}</div>
        </div>
        <FinanceFilters patients={patients} status={status} setStatus={setStatus} patient={patient} setPatient={setPatient} search={search} setSearch={setSearch} count={transactions.length} onRefresh={onRefresh} />
        {loading ? (
          <div className="p-5"><SkeletonTable rows={5} /></div>
        ) : transactions.length === 0 ? (
          <EmptyState icon={tab === "subscriptions" ? <CalendarDays className="h-7 w-7" /> : <ReceiptText className="h-7 w-7" />} title={tab === "subscriptions" ? "Nenhuma mensalidade com este status" : "Nenhum lançamento encontrado"} description={tab === "subscriptions" ? "Crie uma mensalidade para organizar cobranças recorrentes." : "Ajuste os filtros ou registre um novo lançamento financeiro."} action={<Button variant="outline" size="sm" onClick={onCreate}><Plus className="h-4 w-4" /> Novo lançamento</Button>} />
        ) : (
          <FinanceTransactionGrid transactions={transactions} hidden={hidden} renderActions={renderRowActions} />
        )}
      </Card>
    </>
  );
}

function title(tab: FinanceTab) {
  if (tab === "receive") return "Contas a Receber";
  if (tab === "pay") return "Contas a Pagar";
  return "Mensalidades";
}
function subtitle(tab: FinanceTab) {
  if (tab === "receive") return "Cobranças pendentes de pacientes";
  if (tab === "pay") return "Despesas e contas pendentes";
  return "Assinaturas mensais registradas para pacientes";
}
