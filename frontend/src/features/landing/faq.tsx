import { ArrowUpRight } from "lucide-react";
import { faqItems } from "./content";
import { Reveal } from "./motion";

export function Faq() {
  return (
    <section id="faq" className="faq-section">
      <div className="faq-section__inner">
        <Reveal className="faq-section__intro">
          <span className="landing-eyebrow">Perguntas frequentes</span>
          <h2>Clareza antes de entrar na plataforma.</h2>
          <p>
            As respostas abaixo refletem o estado real do projeto e evitam promessas
            sobre recursos que ainda não estão disponíveis.
          </p>
          <a href="#produto">
            Rever demonstração <ArrowUpRight aria-hidden="true" />
          </a>
        </Reveal>

        <div className="faq-section__list">
          {faqItems.map((item, index) => (
            <Reveal key={item.question} delay={Math.min(index * 0.04, 0.16)}>
              <details open={index === 0}>
                <summary>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  {item.question}
                  <i aria-hidden="true" />
                </summary>
                <p>{item.answer}</p>
              </details>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
