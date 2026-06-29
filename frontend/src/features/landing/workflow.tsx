import { workflowSteps } from "./content";

export function Workflow() {
  return (
    <section id="como-funciona" className="landing-section landing-section-muted">
      <div className="landing-heading"><span className="landing-eyebrow">Como funciona</span><h2>Do primeiro cadastro à visão completa da rotina</h2><p>Um fluxo contínuo para reduzir controles paralelos.</p></div>
      <div className="landing-steps">{workflowSteps.map((step) => <article key={step.number} className="landing-card"><strong>{step.number}</strong><h3>{step.title}</h3><p>{step.description}</p></article>)}</div>
    </section>
  );
}
