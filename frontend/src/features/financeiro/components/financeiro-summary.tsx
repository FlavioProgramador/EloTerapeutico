import { ArrowDownRight, ArrowUpRight, CircleDollarSign, Clock3, WalletCards } from "lucide-react";

import { Card } from "@/components/ui/card";
import { SkeletonCard } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatMoney } from "./financeiro-shared";

export type FinanceSummaryMetrics = {
  received: number;
  receivable: number;
  payable: number;
  overdue: number;
  projected: number;
  receivedCount: number;
  receivableCount: number;
  payableCount: number;
};

type Tone = "green" | "red" | "amber";

export function FinanceSummary({ metrics, hidden, loading }: { metrics: FinanceSummaryMetrics; hidden: boolean; loading: boolean }) {
  if (loading) {
    return <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, index) => <SkeletonCard key={index} />)}</div>;
  }

  return (
    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5" aria-label="Resumo financeiro">
      <SummaryCard title="Recebido no Período" value={formatMoney(metrics.received, hidden)} subtitle={`${metrics.receivedCount} receita(s) paga(s)`} icon={WalletCards} tone="green" />
      <SummaryCard title="A Receber" value={formatMoney(metrics.receivable, hidden)} subtitle={`${metrics.receivableCount} cobrança(s) pendente(s)`} icon={ArrowUpRight} tone="green" />
      <SummaryCard title="A Pagar" value={formatMoney(metrics.payable, hidden)} subtitle={`${metrics.payableCount} conta(s) pendente(s)`} icon={ArrowDownRight} tone="red" />
      <SummaryCard title="Vencidos" value={formatMoney(metrics.overdue, hidden)} subtitle="Receitas e despesas em atraso" icon={Clock3} tone="amber" />
      <SummaryCard title="Saldo Projetado" value={formatMoney(metrics.projected, hidden)} subtitle="Recebido + a receber − a pagar" icon={CircleDollarSign} tone={metrics.projected >= 0 ? "green" : "red"} />
    </section>
  );
}

function SummaryCard({ title, value, subtitle, icon: Icon, tone }: { title: string; value: string; subtitle: string; icon: typeof WalletCards; tone: Tone }) {
  const toneClass = tone === "green" ? "text-emerald-500" : tone === "red" ? "text-rose-400" : "text-amber-400";
  return (
    <Card className="min-h-32 border-border bg-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className={cn("mt-2 text-2xl font-bold", toneClass)}>{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <Icon className={cn("h-5 w-5", toneClass)} aria-hidden="true" />
      </div>
    </Card>
  );
}
