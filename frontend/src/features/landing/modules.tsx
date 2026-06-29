import { CheckCircle2 } from "lucide-react";
import { moduleHighlights } from "./content";

export function Modules() {
  return (
    <section className="landing-modules">
      {moduleHighlights.map((item, index) => <article key={item.id} className={index % 2 ? "landing-module reverse" : "landing-module"}><div><span className="landing-eyebrow">{item.eyebrow}</span><h2>{item.title}</h2><p>{item.description}</p><ul>{item.benefits.map((benefit) => <li key={benefit}><CheckCircle2 />{benefit}</li>)}</ul></div><div className="landing-module-preview"><small>VISUAL DEMONSTRATIVO</small>{item.benefits.map((benefit, position) => <span key={benefit}><b>{position + 1}</b>{benefit}</span>)}</div></article>)}
    </section>
  );
}
