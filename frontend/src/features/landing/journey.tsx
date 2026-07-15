import {
  CalendarCheck2,
  LayoutDashboard,
  UserRoundPlus,
  UsersRound,
} from "lucide-react";
import { Reveal } from "./motion";

const steps = [
  [
    "01",
    UserRoundPlus,
    "Configure o acesso",
    "Entre com o perfil adequado à sua responsabilidade.",
  ],
  [
    "02",
    UsersRound,
    "Organize os pacientes",
    "Crie a base usada pela agenda, registros e financeiro.",
  ],
  [
    "03",
    CalendarCheck2,
    "Conduza os atendimentos",
    "Acompanhe sessões, status e evoluções no mesmo fluxo.",
  ],
  [
    "04",
    LayoutDashboard,
    "Visualize a operação",
    "Consulte pendências e movimentações em uma única visão.",
  ],
] as const;

export function Journey() {
  return (
    <section id="fluxo" className="journey-section">
      <div className="journey-section__inner">
        <Reveal className="journey-section__heading">
          <span className="landing-eyebrow">Como funciona</span>
          <h2>Um fluxo simples, sem etapas desconectadas.</h2>
          <p>
            A plataforma acompanha a sequência natural do trabalho clínico e
            administrativo.
          </p>
        </Reveal>
        <div className="journey-line" aria-hidden="true" />
        <div className="journey-steps">
          {steps.map(([number, Icon, title, text], index) => (
            <Reveal
              key={number}
              className={`journey-step ${index % 2 ? "journey-step--lower" : ""}`}
              delay={index * 0.06}
            >
              <span className="journey-step__number">{number}</span>
              <span className="journey-step__icon">
                <Icon aria-hidden="true" />
              </span>
              <h3>{title}</h3>
              <p>{text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
