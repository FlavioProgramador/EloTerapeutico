import { BookOpen, Eye, EyeOff, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type FinanceiroTab = "income" | "expense" | "subscriptions";

interface Props {
  tab: FinanceiroTab;
  hidden: boolean;
  preset: string;
  startDate: string;
  endDate: string;
  onTab: (tab: FinanceiroTab) => void;
  onToggleHidden: () => void;
  onPreset: (preset: string) => void;
  onStartDate: (value: string) => void;
  onEndDate: (value: string) => void;
  onNewLaunch: () => void;
}

const tabs: Array<{ id: FinanceiroTab; label: string }> = [
  { id: "income", label: "A Receber" },
  { id: "expense", label: "A Pagar" },
  { id: "subscriptions", label: "Mensalidades" },
];

export function FinanceiroHeader(props: Props) {
  return (
    <>
      <header className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-extrabold tracking-tight">
              Financeiro
            </h1>
            <BookOpen
              className="h-5 w-5 text-muted-foreground"
              aria-hidden="true"
            />
          </div>
          <p className="mt-1 text-muted-foreground">
            Controle financeiro da clínica
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={props.onToggleHidden}
            leftIcon={
              props.hidden ? (
                <Eye className="h-4 w-4" />
              ) : (
                <EyeOff className="h-4 w-4" />
              )
            }
          >
            {props.hidden ? "Mostrar valores" : "Ocultar valores"}
          </Button>
          <Button
            onClick={props.onNewLaunch}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Novo lançamento
          </Button>
        </div>
      </header>

      <section className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="space-y-1 text-sm font-semibold">
          Período
          <select
            className="block h-11 min-w-44 rounded-lg border border-input bg-card px-3"
            value={props.preset}
            onChange={(event) => props.onPreset(event.target.value)}
          >
            <option value="current">Este mês</option>
            <option value="previous">Mês anterior</option>
            <option value="next30">Próximos 30 dias</option>
            <option value="custom">Personalizado</option>
          </select>
        </label>
        {props.preset === "custom" && (
          <>
            <label className="space-y-1 text-sm font-semibold">
              De
              <input
                className="block h-11 rounded-lg border border-input bg-card px-3"
                type="date"
                value={props.startDate}
                onChange={(event) => props.onStartDate(event.target.value)}
              />
            </label>
            <label className="space-y-1 text-sm font-semibold">
              Até
              <input
                className="block h-11 rounded-lg border border-input bg-card px-3"
                type="date"
                value={props.endDate}
                onChange={(event) => props.onEndDate(event.target.value)}
              />
            </label>
          </>
        )}
      </section>

      <nav
        className="flex gap-1 border-b border-border"
        aria-label="Seções financeiras"
      >
        {tabs.map((item) => (
          <button
            key={item.id}
            onClick={() => props.onTab(item.id)}
            className={cn(
              "border-b-2 px-4 py-3 text-sm font-semibold transition",
              props.tab === item.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </>
  );
}
