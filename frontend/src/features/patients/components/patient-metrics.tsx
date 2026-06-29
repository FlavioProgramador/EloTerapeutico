import type { PatientMetrics } from "../types";

export function PatientMetricsGrid({ metrics }: { metrics?: PatientMetrics }) {
  const cards = [
    ["Total de pacientes", metrics?.total ?? 0],
    ["Em tratamento", metrics?.active ?? 0],
    ["Altas e encerrados", metrics?.discharged ?? 0],
    ["Novos neste mês", metrics?.new_current_month ?? 0],
  ];

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(([label, value]) => (
        <article key={String(label)} className="rounded-xl border border-border bg-card p-4">
          <p className="text-[10px] font-medium text-muted-foreground">{label}</p>
          <strong className="mt-1 block text-xl text-foreground">{value}</strong>
        </article>
      ))}
    </section>
  );
}
