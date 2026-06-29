import { CheckCircle2 } from "lucide-react";
import { featureCards } from "./content";

export function FeatureGrid() {
  return (
    <section id="recursos" className="landing-section">
      <div className="landing-heading"><span className="landing-eyebrow">Recursos conectados</span><h2>Uma operação clínica sem informações espalhadas</h2><p>Cada módulo resolve uma parte da rotina e se conecta aos demais.</p></div>
      <div className="landing-feature-grid">
        {featureCards.map((item) => <article key={item.title} className="landing-card"><CheckCircle2 /><h3>{item.title}</h3><p>{item.description}</p><small>{item.connection}</small></article>)}
      </div>
    </section>
  );
}
