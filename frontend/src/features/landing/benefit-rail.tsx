import {
  CalendarRange,
  LayoutDashboard,
  ShieldCheck,
  UsersRound,
} from "lucide-react";

const items = [
  {
    icon: LayoutDashboard,
    title: "Tudo em um só fluxo",
    text: "Dashboard, pacientes, agenda, prontuários e financeiro conectados.",
  },
  {
    icon: CalendarRange,
    title: "Rotina com contexto",
    text: "Cada atendimento permanece relacionado ao paciente e aos demais módulos.",
  },
  {
    icon: ShieldCheck,
    title: "Acesso por responsabilidade",
    text: "Perfis diferentes visualizam apenas as áreas adequadas à sua função.",
  },
  {
    icon: UsersRound,
    title: "Criado para terapeutas",
    text: "A experiência acompanha o trabalho clínico e administrativo real.",
  },
];

export function BenefitRail() {
  return (
    <section
      className="benefit-rail"
      aria-label="Diferenciais do Elo Terapêutico"
    >
      <div className="benefit-rail__inner">
        {items.map((item) => (
          <article key={item.title} className="benefit-rail__item">
            <span className="benefit-rail__icon">
              <item.icon aria-hidden="true" />
            </span>
            <span>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
