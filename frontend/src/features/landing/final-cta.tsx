import Link from "next/link";
import { ArrowRight, LayoutDashboard } from "lucide-react";
import { ParallaxOrb, Reveal } from "./motion";

export function FinalCta() {
  return (
    <section className="final-cta">
      <ParallaxOrb className="final-cta__orb final-cta__orb--one" speed={24} />
      <ParallaxOrb className="final-cta__orb final-cta__orb--two" speed={16} />
      <Reveal className="final-cta__inner">
        <span className="final-cta__icon">
          <LayoutDashboard aria-hidden="true" />
        </span>
        <span className="landing-eyebrow">Comece pela organização</span>
        <h2>
          Menos ferramentas separadas.
          <br />
          Mais clareza para cuidar.
        </h2>
        <p>
          Crie seu acesso e conheça os módulos já disponíveis no Elo
          Terapêutico.
        </p>
        <div className="final-cta__actions">
          <Link href="/register">
            Testar grátis <ArrowRight aria-hidden="true" />
          </Link>
          <Link href="/login">Já tenho acesso</Link>
        </div>
      </Reveal>
    </section>
  );
}
