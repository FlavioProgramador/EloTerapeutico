import {
  Activity,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { Reveal } from "./motion";

const points = [
  {
    icon: LockKeyhole,
    title: "Campos sensíveis protegidos",
    text: "O projeto possui uma camada própria para tratamento de informações clínicas sensíveis.",
  },
  {
    icon: UsersRound,
    title: "Permissões por responsabilidade",
    text: "As áreas disponíveis variam conforme o papel do usuário dentro da operação.",
  },
  {
    icon: Activity,
    title: "Rastreabilidade operacional",
    text: "A arquitetura inclui trilha de auditoria para acompanhar ações relevantes.",
  },
];

export function TrustSection() {
  return (
    <section id="seguranca" className="trust-section">
      <div className="trust-section__inner">
        <Reveal className="trust-section__visual">
          <div className="trust-orbit trust-orbit--outer" aria-hidden="true" />
          <div className="trust-orbit trust-orbit--inner" aria-hidden="true" />
          <div className="trust-core">
            <span>
              <ShieldCheck />
            </span>
            <strong>Proteção em camadas</strong>
            <small>Arquitetura, acesso e rastreabilidade</small>
          </div>
          <span className="trust-node trust-node--one">
            <KeyRound />
          </span>
          <span className="trust-node trust-node--two">
            <UsersRound />
          </span>
          <span className="trust-node trust-node--three">
            <Activity />
          </span>
        </Reveal>

        <Reveal className="trust-section__copy" delay={0.08}>
          <span className="landing-eyebrow">Segurança e responsabilidade</span>
          <h2>Privacidade tratada como parte da arquitetura.</h2>
          <p>
            O Elo Terapêutico adota controles técnicos para reduzir exposição
            indevida e separar responsabilidades. A conformidade completa também
            depende da configuração, da operação e dos processos da clínica.
          </p>

          <div className="trust-points">
            {points.map((point) => (
              <article key={point.title}>
                <span>
                  <point.icon aria-hidden="true" />
                </span>
                <div>
                  <strong>{point.title}</strong>
                  <small>{point.text}</small>
                </div>
              </article>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
