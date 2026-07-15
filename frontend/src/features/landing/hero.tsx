import Link from "next/link";
import { ArrowRight, Play } from "lucide-react";
import { AnimatedCounter, Reveal } from "./motion";
import { EloSvg } from "./elo-svg";

const stats = [
  { value: 5, suffix: "h+", label: "recuperadas por semana" },
  { value: 100, suffix: "%", label: "LGPD compliance" },
  { value: 1, suffix: "", label: "dia para começar" },
];

export function Hero() {
  return (
    <section id="conteudo" className="hero-dark">
      <div className="hero-dark__texture" aria-hidden="true" />

      <div className="hero-dark__inner">
        <Reveal className="hero-dark__copy">
          <span className="landing-eyebrow">
            O sistema feito para terapeutas
          </span>
          <h1>
            Gestão completa.
            <br />
            Mais tempo para <em>cuidar.</em>
          </h1>
          <p>
            Organize agenda, prontuários, pacientes e financeiro em um só lugar.
            Menos burocracia para manter o foco no acompanhamento de quem você
            atende.
          </p>

          <div className="hero-dark__actions">
            <Link href="/register" className="hero-dark__primary">
              Testar grátis{" "}
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <a href="#produto" className="hero-dark__secondary">
              <Play className="h-4 w-4" aria-hidden="true" />
              Ver demonstração
            </a>
          </div>
        </Reveal>

        <Reveal className="hero-dark__visual" delay={0.1}>
          <EloSvg size="hero" className="hero-dark__elo" />
        </Reveal>
      </div>

      <Reveal className="hero-dark__stats" delay={0.2}>
        {stats.map((stat) => (
          <article key={stat.label} className="hero-dark__stat">
            <AnimatedCounter
              target={stat.value}
              suffix={stat.suffix}
              className="hero-dark__stat-value"
            />
            <span className="hero-dark__stat-label">{stat.label}</span>
          </article>
        ))}
      </Reveal>
    </section>
  );
}
