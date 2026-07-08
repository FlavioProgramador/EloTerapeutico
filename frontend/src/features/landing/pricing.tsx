import Link from "next/link";
import { Check, ArrowRight } from "lucide-react";
import { Reveal } from "./motion";

const plans = [
  {
    name: "Individual",
    price: "Grátis",
    priceNote: "para começar",
    description: "Para terapeutas autônomos que querem organizar sua prática.",
    features: [
      "Agenda com lembretes",
      "Prontuário eletrônico",
      "Controle financeiro básico",
      "Suporte por e-mail",
    ],
    cta: "Testar grátis",
    ctaHref: "/register",
    highlighted: false,
  },
  {
    name: "Clínica",
    price: "Em breve",
    priceNote: "",
    description: "Para pequenas clínicas com múltiplos profissionais.",
    features: [
      "Tudo do plano Individual",
      "Múltiplos terapeutas",
      "Perfis e permissões",
      "Relatórios consolidados",
      "Suporte prioritário",
    ],
    cta: "Em breve",
    ctaHref: "#",
    highlighted: true,
  },
];

export function Pricing() {
  return (
    <section id="precos" className="pricing-section">
      <div className="pricing-section__inner">
        <Reveal className="pricing-section__heading">
          <span className="landing-eyebrow">Planos e preços</span>
          <h2>Simples, sem surpresas.</h2>
          <p>
            Comece grátis. Pague apenas quando precisar de mais. Sem taxas escondidas por paciente.
          </p>
        </Reveal>

        <div className="pricing-section__grid">
          {plans.map((plan, i) => (
            <Reveal
              key={plan.name}
              className={`pricing-card ${plan.highlighted ? "pricing-card--highlighted" : ""}`}
              delay={i * 0.06}
            >
              <div className="pricing-card__header">
                <span className="pricing-card__name">{plan.name}</span>
                <div className="pricing-card__price">
                  <strong>{plan.price}</strong>
                  {plan.priceNote && <small>{plan.priceNote}</small>}
                </div>
                <p className="pricing-card__desc">{plan.description}</p>
              </div>
              <ul className="pricing-card__features">
                {plan.features.map((f) => (
                  <li key={f}>
                    <Check aria-hidden="true" />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href={plan.ctaHref}
                className={`pricing-card__cta ${plan.highlighted ? "pricing-card__cta--primary" : ""}`}
              >
                {plan.cta}
                <ArrowRight aria-hidden="true" />
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
