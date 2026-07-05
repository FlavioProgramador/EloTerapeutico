import { CalendarDays } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FinanceTab } from "./financeiro-shared";

export function FinanceTabs({ tab, onChange }: { tab: FinanceTab; onChange: (tab: FinanceTab) => void }) {
  return (
    <nav className="flex gap-1 border-b border-border" aria-label="Seções financeiras">
      <Tab active={tab === "receive"} onClick={() => onChange("receive")}>A Receber</Tab>
      <Tab active={tab === "pay"} onClick={() => onChange("pay")}>A Pagar</Tab>
      <Tab active={tab === "subscriptions"} onClick={() => onChange("subscriptions")}><CalendarDays className="h-4 w-4" /> Mensalidades</Tab>
    </nav>
  );
}

function Tab({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return <button type="button" onClick={onClick} className={cn("flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-medium", active ? "border-primary text-foreground" : "border-transparent text-muted-foreground")}>{children}</button>;
}
