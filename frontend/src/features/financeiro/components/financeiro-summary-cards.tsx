import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Wallet,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { SkeletonCard } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { formatCurrency } from "../financeiro-formatters";
import type { FinancialDashboardSummary } from "../services/financeiro-dashboard.service";

interface Props {
  summary?: FinancialDashboardSummary;
  isLoading: boolean;
  hidden: boolean;
}

const cards = [
  {
    key: "received",
    count: "received_count",
    label: "Recebido no período",
    icon: Wallet,
    tone: "text-emerald-500",
  },
  {
    key: "receivable",
    count: "receivable_count",
    label: "A receber",
    icon: ArrowUpRight,
    tone: "text-emerald-500",
  },
  {
    key: "payable",
    count: "payable_count",
    label: "A pagar",
    icon: ArrowDownRight,
    tone: "text-rose-500",
  },
  {
    key: "overdue",
    count: "overdue_receivable_count",
    label: "Vencidos",
    icon: AlertCircle,
    tone: "text-amber-500",
  },
  {
    key: "projected_balance",
    count: null,
    label: "Saldo projetado",
    icon: DollarSign,
    tone: "text-primary",
  },
] as const;

export function FinanceiroSummaryCards({ summary, isLoading, hidden }: Props) {
  if (isLoading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map((card) => (
          <SkeletonCard key={card.key} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map(({ key, count, label, icon: Icon, tone }) => {
        const value = summary?.[key] ?? "0";
        const quantity = count ? Number(summary?.[count] ?? 0) : null;
        return (
          <Card key={key} className="min-h-32 p-5">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-semibold text-muted-foreground">
                {label}
              </p>
              <Icon className={cn("h-4 w-4", tone)} aria-hidden="true" />
            </div>
            <p
              className={cn(
                "mt-3 text-2xl font-bold tracking-tight",
                key === "projected_balance" && Number(value) >= 0
                  ? "text-emerald-500"
                  : key === "projected_balance"
                    ? "text-rose-500"
                    : tone,
              )}
            >
              {formatCurrency(value, hidden)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {quantity === null
                ? "Considerando entradas e saídas pendentes"
                : `${quantity} registro${quantity === 1 ? "" : "s"}`}
            </p>
          </Card>
        );
      })}
    </div>
  );
}
