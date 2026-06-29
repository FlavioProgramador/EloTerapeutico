import Image from "next/image";
import Link from "next/link";
import { ArrowRight, CalendarCheck2, CheckCircle2 } from "lucide-react";
import { ParallaxOrb, Reveal } from "./motion";

export function Hero() {
  const highlights = ["Agenda integrada", "Prontuários organizados", "Financeiro conectado"];

  return (
    <section id="conteudo" className="hero-premium">
      <div className="hero-premium__texture" aria-hidden="true" />
      <ParallaxOrb className="hero-premium__orb hero-premium__orb--one" speed={34} />
      <ParallaxOrb className="hero-premium__orb hero-premium__orb--two" speed={18} />

      <div className="hero-premium__inner">
        <Reveal className="hero-premium__copy">
          <span className="landing-eyebrow">O sistema feito para terapeutas</span>
          <h1>
            Gestão completa.
            <br />
            Mais tempo para <em>cuidar.</em>
          </h1>
          <p>
            Organize agenda, prontuários, pacientes e financeiro em um só lugar.
            Menos burocracia para manter o foco no acompanhamento de quem você atende.
          </p>

          <div className="hero-premium__actions">
            <Link href="/register" className="hero-premium__primary">
              Começar agora <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <a href="#produto" className="hero-premium__secondary">
              Ver a plataforma
            </a>
          </div>

          <div className="hero-premium__checks" aria-label="Principais áreas da plataforma">
            {highlights.map((item) => (
              <span key={item}>
                <CheckCircle2 aria-hidden="true" />
                {item}
              </span>
            ))}
          </div>
        </Reveal>

        <Reveal className="hero-premium__media" delay={0.08}>
          <div className="hero-premium__photo">
            <Image
              src="/terapeuta_acolhedora.png"
              alt="Terapeuta em um ambiente acolhedor de atendimento"
              fill
              priority
              sizes="(max-width: 1024px) 100vw, 48vw"
            />
            <div className="hero-premium__shade" aria-hidden="true" />
          </div>

          <div className="hero-premium__floating-card">
            <span className="hero-premium__floating-icon">
              <CalendarCheck2 aria-hidden="true" />
            </span>
            <span>
              <strong>Sua agenda organizada</strong>
              <small>Contexto e rotina no mesmo fluxo</small>
            </span>
          </div>

          <div className="hero-premium__signal" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
