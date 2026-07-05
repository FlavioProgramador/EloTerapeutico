"use client";

import { FinanceiroBillingModal } from "./components/financeiro-billing-modal";
import { FinanceiroHeader } from "./components/financeiro-header";
import { FinanceiroSubscriptionModal } from "./components/financeiro-subscription-modal";
import { FinanceiroSubscriptionsPanel } from "./components/financeiro-subscriptions-panel";
import { FinanceiroSummaryCards } from "./components/financeiro-summary-cards";
import { FinanceiroTransactionModal } from "./components/financeiro-transaction-modal";
import { FinanceiroTransactionsPanel } from "./components/financeiro-transactions-panel";
import { useFinanceiroPage } from "./hooks/use-financeiro-page";

export function FinanceiroDashboard() {
  const page = useFinanceiroPage();
  const newLaunch = () => page.setModal(page.tab === "subscriptions" ? "subscription" : "transaction");

  return (
    <div className="space-y-5">
      <FinanceiroHeader tab={page.tab} hidden={page.hidden} preset={page.preset} startDate={page.startDate} endDate={page.endDate} onTab={page.setTab} onToggleHidden={page.toggleHidden} onPreset={page.changePreset} onStartDate={page.setStartDate} onEndDate={page.setEndDate} onNewLaunch={newLaunch} />
      <FinanceiroSummaryCards summary={page.summary.data} isLoading={page.summary.isLoading} hidden={page.hidden} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        {page.tab === "subscriptions" ? (
          <select className="h-10 rounded-lg border border-input bg-card px-3 text-sm" value={page.subscriptionStatus} onChange={(event) => page.setSubscriptionStatus(event.target.value)}>
            <option value="active">Ativas</option><option value="paused">Pausadas</option><option value="ended">Encerradas</option><option value="cancelled">Canceladas</option>
          </select>
        ) : (
          <select className="h-10 rounded-lg border border-input bg-card px-3 text-sm" value={page.statusFilter} onChange={(event) => page.setStatusFilter(event.target.value)}>
            <option value="all">Todos os status</option><option value="pending">Pendentes</option><option value="paid">Pagos</option><option value="cancelled">Cancelados</option>
          </select>
        )}
      </div>

      {page.tab === "subscriptions" ? (
        <FinanceiroSubscriptionsPanel subscriptions={page.subscriptions.data ?? []} isLoading={page.subscriptions.isLoading} hidden={page.hidden} onCreate={() => page.setModal("subscription")} onStatusChange={(id, status) => page.updateSubscription.mutate({ id, status })} actionPending={page.updateSubscription.isPending} />
      ) : (
        <FinanceiroTransactionsPanel mode={page.tab} transactions={page.visibleTransactions} isLoading={page.transactions.isLoading} hidden={page.hidden} onCreate={() => page.setModal("transaction")} onGenerateCharges={page.tab === "income" ? () => page.setModal("billing") : undefined} onMarkPaid={(id) => page.markPaid.mutate({ id })} onCancel={(id) => page.cancel.mutate(id)} actionPending={page.markPaid.isPending || page.cancel.isPending} />
      )}

      <FinanceiroTransactionModal open={page.modal === "transaction"} mode={page.tab === "expense" ? "expense" : "income"} patients={page.patients} onClose={() => page.setModal(null)} />
      <FinanceiroSubscriptionModal open={page.modal === "subscription"} patients={page.patients} onClose={() => page.setModal(null)} />
      <FinanceiroBillingModal open={page.modal === "billing"} appointments={page.unbilled.data ?? []} onClose={() => page.setModal(null)} />
    </div>
  );
}
