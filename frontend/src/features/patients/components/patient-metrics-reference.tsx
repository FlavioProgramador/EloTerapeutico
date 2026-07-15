import { Cake, UserCheck, UsersRound } from "lucide-react";

interface Props {
  total: number;
  active: number;
  birthdays: number;
  loading: boolean;
}

export function PatientMetricsReference(props: Props) {
  const cards = [
    {
      label: "Total de pacientes",
      value: props.total,
      detail: "Cadastrados na clínica",
      Icon: UsersRound,
    },
    {
      label: "Pacientes ativos",
      value: props.active,
      detail: "Em acompanhamento",
      Icon: UserCheck,
    },
    {
      label: "Aniversariantes",
      value: props.birthdays,
      detail: "Neste mês",
      Icon: Cake,
    },
  ];

  return (
    <section
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
      aria-label="Indicadores de pacientes"
    >
      {cards.map(({ label, value, detail, Icon }) => (
        <article
          key={label}
          className="min-h-32 rounded-xl border border-border bg-card p-5 shadow-xs"
        >
          <div className="flex h-full items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold text-foreground">{label}</p>
              <strong className="mt-4 block text-2xl font-bold text-primary">
                {props.loading ? "—" : value}
              </strong>
              <p className="mt-1 text-[11px] text-muted-foreground">{detail}</p>
            </div>
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </span>
          </div>
        </article>
      ))}
    </section>
  );
}
