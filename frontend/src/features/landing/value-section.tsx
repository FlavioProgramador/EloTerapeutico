"use client";

import {
  ArrowRight,
  Check,
  Layers3,
  Link2,
  X,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
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
  const reduceMotion = useReducedMotion();

  const leftAnim = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, x: -8 },
        whileInView: { opacity: 1, x: 0 },
        viewport: { once: true, amount: 0.16 },
        transition: { duration: 0.58, delay: 0.05, ease: [0.22, 1, 0.36, 1] as const },
      };

  const rightAnim = reduceMotion
    ? {}
    : {
        initial: { opacity: 0, x: 8 },
        whileInView: { opacity: 1, x: 0 },
        viewport: { once: true, amount: 0.16 },
        transition: { duration: 0.58, delay: 0.05, ease: [0.22, 1, 0.36, 1] as const },
      };

  return (
    <section className="value-section">
      <div className="value-section__inner">
        <Reveal className="value-section__heading">
          <div className="value-section__heading-left">
            <span className="landing-eyebrow">O diferencial está na conexão</span>
            <p className="value-section__heading-desc">
              A plataforma não substitui o trabalho clínico. Ela reduz a fragmentação
              administrativa que cerca esse trabalho.
            </p>
          </div>
          <div className="value-section__heading-right">
            <h2>Ferramentas genéricas guardam informações. O Elo organiza relações.</h2>
          </div>
        </Reveal>

        <div className="value-comparison">
          <motion.div
            className="value-comparison__side value-comparison__side--manual"
            {...leftAnim}
          >
            <span className="value-comparison__label">Controles separados</span>
            <h3>Mais pontos para conferir.</h3>
            <ul>
              {manualItems.map((item) => (
                <li key={item}><X aria-hidden="true" />{item}</li>
              ))}
            </ul>
          </motion.div>

          <div className="value-comparison__bridge" aria-hidden="true">
            <span><ArrowRight /></span>
          </div>

          <motion.div
            className="value-comparison__side value-comparison__side--connected"
            {...rightAnim}
          >
            <span className="value-comparison__label">Elo Terapêutico</span>
            <h3>Um fluxo com continuidade.</h3>
            <ul>
              {connectedItems.map((item) => (
                <li key={item}><Check aria-hidden="true" />{item}</li>
              ))}
            </ul>
          </motion.div>
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
