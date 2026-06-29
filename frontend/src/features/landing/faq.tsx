import { faqItems } from "./content";

export function Faq() {
  return (
    <section id="faq" className="landing-section">
      <div className="landing-heading"><span className="landing-eyebrow">Perguntas frequentes</span><h2>Informações claras antes de começar</h2></div>
      <div className="landing-faq">{faqItems.map((item, index) => <details key={item.question} open={index === 0}><summary>{item.question}</summary><p>{item.answer}</p></details>)}</div>
    </section>
  );
}
