import { AnimatedCounter, Reveal } from "./motion";

const metrics = [
  { value: 5, suffix: "h+", label: "recuperadas por semana em média" },
  { value: 100, suffix: "%", label: "dos dados protegidos por criptografia" },
  { value: 1, suffix: "", label: "dia para ter o consultório organizado" },
];

export function SocialProof() {
  return (
    <section className="social-proof" aria-label="Números que importam">
      <div className="social-proof__inner">
        <Reveal className="social-proof__heading">
          <span className="landing-eyebrow">Prova social</span>
          <h2>Números reais de uma gestão que funciona.</h2>
        </Reveal>
        <div className="social-proof__grid">
          {metrics.map((metric) => (
            <Reveal key={metric.label} className="social-proof__card">
              <AnimatedCounter
                target={metric.value}
                suffix={metric.suffix}
                className="social-proof__number"
              />
              <span className="social-proof__label">{metric.label}</span>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
