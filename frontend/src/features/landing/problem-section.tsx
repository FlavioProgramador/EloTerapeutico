import {
  CalendarClock,
  FileSpreadsheet,
  FileText,
  Link2,
} from "lucide-react";
import { Reveal } from "./motion";

const fragments = [
  {
    icon: CalendarClock,
    title: "Agenda isolada",
    text: "Horários sem o contexto completo do paciente.",
    className: "problem-map__node--agenda",
  },
  {
    icon: FileText,
    title: "Anotações dispersas",
    text: "Registros difíceis de localizar e relacionar.",
    className: "problem-map__node--records",
  },
  {
    icon: FileSpreadsheet,
    title: "Planilhas paralelas",
    text: "Cobranças separadas da rotina de atendimento.",
    className: "problem-map__node--finance",
  },
];

export function ProblemSection() {
  return (
    <section className="problem-section">
      <div className="problem-section__inner">
        <Reveal className="problem-section__copy">
          <span className="landing-eyebrow">O problema não é falta de ferramenta</span>
          <h2>É precisar reconstruir o contexto a cada tarefa.</h2>
          <p>
            Quando agenda, registros e financeiro vivem em lugares diferentes, o
            profissional perde tempo procurando informações e repetindo processos.
            O Elo Terapêutico aproxima essas áreas sem confundir suas responsabilidades.
          </p>
          <div className="problem-section__quote">
            <span>Menos troca de contexto.</span>
            <strong>Mais continuidade na rotina.</strong>
          </div>
        </Reveal>

        <Reveal className="problem-map" delay={0.08}>
          <div className="problem-map__lines" aria-hidden="true" />
          {fragments.map((fragment) => (
            <article
              key={fragment.title}
              className={`problem-map__node ${fragment.className}`}
            >
              <fragment.icon aria-hidden="true" />
              <strong>{fragment.title}</strong>
              <small>{fragment.text}</small>
            </article>
          ))}

          <div className="problem-map__center">
            <span className="problem-map__center-icon">
              <Link2 aria-hidden="true" />
            </span>
            <strong>Elo Terapêutico</strong>
            <small>Um fluxo conectado</small>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
