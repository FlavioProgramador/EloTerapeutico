import { Activity, BadgeCheck, UserRoundPlus, UsersRound } from "lucide-react";

import type { PatientMetrics } from "../types";

export function PatientMetricsGrid({ metrics }: { metrics?: PatientMetrics }) {
  const newDifference =
    (metrics?.new_current_month ?? 0) - (metrics?.new_previous_month ?? 0);
  const cards = [
    {
      label: "Total de pacientes",
      value: metrics?.total ?? 0,
      detail: "Cadastros autorizados",
      icon: UsersRound,
    },
    {
      label: "Em tratamento",
      value: metrics?.active ?? 0,
      detail: `${metrics?.active_percentage ?? 0}% do total`,
      icon: Activity,
    },
    {
      label: "Altas e encerrados",
      value: metrics?.discharged ?? 0,
      detail: `${metrics?.discharged_percentage ?? 0}% do total`,
      icon: BadgeCheck,
    },
    {
      label: "Novos neste mês",
      value: metrics?.new_current_month ?? 0,
      detail:
        newDifference === 0
          ? "Mesmo resultado do mês anterior"
          : `${newDifference > 0 ? "+" : ""}${newDifference} em relação ao mês anterior`,
      icon: UserRoundPlus,
    },
  ];

  return (
    <section
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      aria-label="Indicadores de pacientes"
    >
      {cards.map(({ label, value, detail, icon: Icon }) => (
        <article
          key={label}
          className="rounded-xl border border-border bg-card p-4 shadow-xs"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-muted-foreground">
                {label}
              </p>
              <strong className="mt-1 block text-3xl font-extrabold text-foreground">
                {value}
              </strong>
              <p className="mt-2 text-xs text-muted-foreground">{detail}</p>
            </div>
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </span>
          </div>
        </article>
      ))}
    </section>
  );
}
