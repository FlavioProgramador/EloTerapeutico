import { cn } from "@/lib/utils";

export type FinanceiroTab = "income" | "expense" | "subscriptions";

const tabs: Array<{ id: FinanceiroTab; label: string }> = [
  { id: "income", label: "A Receber" },
  { id: "expense", label: "A Pagar" },
  { id: "subscriptions", label: "Mensalidades" },
];

interface Props {
  value: FinanceiroTab;
  onChange: (tab: FinanceiroTab) => void;
}

export function FinanceiroTabs({ value, onChange }: Props) {
  return (
    <nav className="flex gap-1 border-b border-border" aria-label="Seções financeiras">
      {tabs.map((item) => (
        <button
          key={item.id}
          type="button"
          onClick={() => onChange(item.id)}
          className={cn(
            "border-b-2 px-4 py-3 text-sm font-semibold transition",
            value === item.id
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
