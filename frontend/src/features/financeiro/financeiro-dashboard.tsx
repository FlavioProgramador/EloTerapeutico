"use client";

import { FinanceiroBillingModal } from "./components/financeiro-billing-modal";
import { FinanceiroNewBillingModal } from "./components/financeiro-new-billing-modal";
import { FinanceiroHeader } from "./components/financeiro-header";
import { FinanceiroMarkPaidModal } from "./components/financeiro-mark-paid-modal";
import { FinanceiroSubscriptionModal } from "./components/financeiro-subscription-modal";
import { FinanceiroSubscriptionsPanel } from "./components/financeiro-subscriptions-panel";
import { FinanceiroSummaryCards } from "./components/financeiro-summary-cards";
import { FinanceiroTransactionModal } from "./components/financeiro-transaction-modal";
import { FinanceiroTransactionsPanel } from "./components/financeiro-transactions-panel";
import { useFinanceiroPage } from "./hooks/use-financeiro-page";

export function FinanceiroDashboard() {
  const page = useFinanceiroPage();
  const newLaunch = () =>
    page.setModal(
      page.tab === "subscriptions" ? "subscription" : "transaction",
    );

  return (
    <div className="space-y-5">
      <FinanceiroHeader
        tab={page.tab}
        hidden={page.hidden}
        preset={page.preset}
        startDate={page.startDate}
        endDate={page.endDate}
        onTab={page.setTab}
        onToggleHidden={page.toggleHidden}
        onPreset={page.changePreset}
        onStartDate={page.setStartDate}
        onEndDate={page.setEndDate}
        onNewLaunch={newLaunch}
      />
      <FinanceiroSummaryCards
        summary={page.summary.data}
        isLoading={page.summary.isLoading}
        hidden={page.hidden}
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        {page.tab === "subscriptions" ? (
          <select
            className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
            value={page.subscriptionStatus}
            onChange={(event) => page.setSubscriptionStatus(event.target.value)}
          >
            <option value="active">Ativas</option>
            <option value="paused">Pausadas</option>
            <option value="ended">Encerradas</option>
            <option value="cancelled">Canceladas</option>
          </select>
        ) : (
          <select
            className="h-10 rounded-lg border border-input bg-card px-3 text-sm"
            value={page.statusFilter}
            onChange={(event) => page.setStatusFilter(event.target.value)}
          >
            <option value="all">Todos os status</option>
            <option value="pending">Pendentes</option>
            <option value="paid">Pagos</option>
            <option value="cancelled">Cancelados</option>
          </select>
        )}
      </div>

      {page.tab === "subscriptions" ? (
        <FinanceiroSubscriptionsPanel
          subscriptions={page.subscriptions.data ?? []}
          isLoading={page.subscriptions.isLoading}
          hidden={page.hidden}
          onCreate={() => page.setModal("subscription")}
          onStatusChange={(id, status) =>
            page.updateSubscription.mutate({ id, status })
          }
          actionPending={page.updateSubscription.isPending}
        />
      ) : (
        <FinanceiroTransactionsPanel
          mode={page.tab}
          transactions={page.visibleTransactions}
          isLoading={page.transactions.isLoading}
          hidden={page.hidden}
          onCreate={() => page.setModal("transaction")}
          onGenerateCharges={
            page.tab === "income" ? () => page.setModal("billing") : undefined
          }
          onNewCharge={
            page.tab === "income"
              ? () => page.setModal("new-billing")
              : undefined
          }
          onMarkPaid={(id) => {
            const tx = page.visibleTransactions.find((t) => t.id === id);
            if (tx) page.setMarkPaidTransaction(tx);
          }}
          onCancel={(id) => page.cancel.mutate(id)}
          onDelete={(id) => page.remove.mutate(id)}
          onRefund={(id) => page.refund.mutate(id)}
          actionPending={
            page.markPaid.isPending ||
            page.cancel.isPending ||
            page.remove.isPending ||
            page.refund.isPending
          }
        />
      )}

      <FinanceiroTransactionModal
        open={page.modal === "transaction"}
        mode={page.tab === "expense" ? "expense" : "income"}
        patients={page.patients}
        onClose={() => page.setModal(null)}
      />
      <FinanceiroSubscriptionModal
        open={page.modal === "subscription"}
        patients={page.patients}
        onClose={() => page.setModal(null)}
      />
      <FinanceiroBillingModal
        open={page.modal === "billing"}
        appointments={page.unbilled.data ?? []}
        onClose={() => page.setModal(null)}
      />
      <FinanceiroNewBillingModal
        open={page.modal === "new-billing"}
        patients={page.patients}
        unbilled={page.unbilled.data ?? []}
        onClose={() => page.setModal(null)}
      />
      <FinanceiroMarkPaidModal
        transaction={page.markPaidTransaction}
        onClose={() => page.setMarkPaidTransaction(null)}
        onConfirm={(data) => {
          page.markPaid.mutate(data, {
            onSuccess: () => page.setMarkPaidTransaction(null),
          });
        }}
        isPending={page.markPaid.isPending}
      />
    </div>
  );
}
