import {
  ArrowRight,
  Check,
  Layers3,
  Link2,
  X,
} from "lucide-react";
import { Reveal } from "./motion";

const manualItems = [
  "Agenda em uma ferramenta",
  "Registros em outro lugar",
  "Financeiro em planilhas",
  "Contexto reconstruído manualmente",
];

const connectedItems = [
  "Paciente como base do fluxo",
  "Atendimento ligado ao prontuário",
  "Financeiro próximo da operação",
  "Dashboard para acompanhar pendências",
];

export function ValueSection() {
  return (
    <section className="value-section">
      <div className="value-section__inner">
        <Reveal className="value-section__heading">
          <span className="landing-eyebrow">O diferencial está na conexão</span>
          <h2>Ferramentas genéricas guardam informações. O Elo organiza relações.</h2>
          <p>
            A plataforma não substitui o trabalho clínico. Ela reduz a fragmentação
            administrativa que cerca esse trabalho.
          </p>
        </Reveal>

        <div className="value-comparison">
          <Reveal className="value-comparison__side value-comparison__side--manual">
            <span className="value-comparison__label">Controles separados</span>
            <h3>Mais pontos para conferir.</h3>
            <ul>
              {manualItems.map((item) => (
                <li key={item}><X aria-hidden="true" />{item}</li>
              ))}
            </ul>
          </Reveal>

          <div className="value-comparison__bridge" aria-hidden="true">
            <span><ArrowRight /></span>
          </div>

          <Reveal className="value-comparison__side value-comparison__side--connected" delay={0.08}>
            <span className="value-comparison__label">Elo Terapêutico</span>
            <h3>Um fluxo com continuidade.</h3>
            <ul>
              {connectedItems.map((item) => (
                <li key={item}><Check aria-hidden="true" />{item}</li>
              ))}
            </ul>
          </Reveal>
        </div>

        <div className="value-numbers">
          <article><Layers3 /><strong>5</strong><span>áreas principais conectadas</span></article>
          <article><Link2 /><strong>1</strong><span>visão operacional compartilhada</span></article>
          <article><Check /><strong>3</strong><span>perfis com responsabilidades distintas</span></article>
        </div>
      </div>
    </section>
  );
}
