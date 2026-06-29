import { LockKeyhole } from "lucide-react";
import { securityPoints } from "./content";

export function Security() {
  return (
    <section id="seguranca" className="landing-section landing-section-muted">
      <div className="landing-heading"><span className="landing-eyebrow">Segurança e responsabilidade</span><h2>Privacidade tratada como parte da arquitetura</h2><p>O projeto adota controles técnicos para reduzir exposição indevida. A conformidade também depende da configuração e dos processos da clínica.</p></div>
      <div className="landing-security">{securityPoints.map((item) => <article key={item.title} className="landing-card"><LockKeyhole /><h3>{item.title}</h3><p>{item.description}</p></article>)}</div>
    </section>
  );
}
