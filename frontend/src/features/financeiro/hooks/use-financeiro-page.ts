"use client";

import { useEffect, useMemo, useState } from "react";

import { usePatients } from "@/features/patients/hooks/use-patients";
import { currentMonthRange } from "../financeiro-formatters";
import type { FinanceiroTab } from "../components/financeiro-header";
import {
  useFinanceiroDashboard,
  useMonthlySubscriptions,
  useUpdateMonthlySubscriptionStatus,
} from "./use-financeiro-dashboard";
import {
  useCancelTransaction,
  useMarkAsPaid,
  useTransactions,
  useUnbilledAppointments,
  useDeleteTransaction,
  useRefundTransaction,
} from "./use-financeiro";

export type FinanceiroModal =
  | "transaction"
  | "subscription"
  | "billing"
  | "new-billing"
  | null;
import type { FinancialTransaction } from "@/types";

function range(preset: string) {
  const now = new Date();
  if (preset === "previous") {
    return {
      startDate: new Date(now.getFullYear(), now.getMonth() - 1, 1)
        .toISOString()
        .slice(0, 10),
      endDate: new Date(now.getFullYear(), now.getMonth(), 0)
        .toISOString()
        .slice(0, 10),
    };
  }
  if (preset === "next30") {
    const end = new Date(now);
    end.setDate(end.getDate() + 30);
    return {
      startDate: now.toISOString().slice(0, 10),
      endDate: end.toISOString().slice(0, 10),
    };
  }
  return currentMonthRange();
}

export function useFinanceiroPage() {
  const initial = currentMonthRange();
  const [tab, setTab] = useState<FinanceiroTab>("income");
  const [modal, setModal] = useState<FinanceiroModal>(null);
  const [markPaidTransaction, setMarkPaidTransaction] =
    useState<FinancialTransaction | null>(null);
  const [hidden, setHidden] = useState(false);
  const [preset, setPreset] = useState("current");
  const [startDate, setStartDate] = useState(initial.startDate);
  const [endDate, setEndDate] = useState(initial.endDate);
  const [statusFilter, setStatusFilter] = useState("all");
  const [subscriptionStatus, setSubscriptionStatus] = useState("active");

  useEffect(
    () => setHidden(localStorage.getItem("financeiro-hide-values") === "true"),
    [],
  );
  const toggleHidden = () =>
    setHidden((value) => {
      localStorage.setItem("financeiro-hide-values", String(!value));
      return !value;
    });
  const changePreset = (value: string) => {
    setPreset(value);
    if (value !== "custom") {
      const next = range(value);
      setStartDate(next.startDate);
      setEndDate(next.endDate);
    }
  };

  const summary = useFinanceiroDashboard(startDate, endDate);
  const patients = usePatients({ status: "active" });
  const transactions = useTransactions({
    transaction_type: tab === "subscriptions" ? undefined : tab,
    payment_status: statusFilter === "all" ? undefined : statusFilter,
  });
  const subscriptions = useMonthlySubscriptions(subscriptionStatus);
  const unbilled = useUnbilledAppointments();
  const markPaid = useMarkAsPaid();
  const cancel = useCancelTransaction();
  const updateSubscription = useUpdateMonthlySubscriptionStatus();
  const remove = useDeleteTransaction();
  const refund = useRefundTransaction();

  const visibleTransactions = useMemo(
    () =>
      (transactions.data ?? []).filter((item) => {
        if (tab === "subscriptions" || item.type !== tab) return false;
        const itemDate =
          item.due_date || item.payment_date || item.created_at.slice(0, 10);
        return itemDate >= startDate && itemDate <= endDate;
      }),
    [transactions.data, tab, startDate, endDate],
  );

  return {
    tab,
    setTab,
    modal,
    setModal,
    markPaidTransaction,
    setMarkPaidTransaction,
    hidden,
    toggleHidden,
    preset,
    changePreset,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
    statusFilter,
    setStatusFilter,
    subscriptionStatus,
    setSubscriptionStatus,
    summary,
    transactions,
    visibleTransactions,
    subscriptions,
    unbilled,
    markPaid,
    cancel,
    updateSubscription,
    remove,
    refund,
    patients: patients.data?.results ?? [],
  };
}
