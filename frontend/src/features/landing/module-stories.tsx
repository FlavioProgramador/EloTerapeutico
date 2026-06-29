import {
  CalendarDays,
  CheckCircle2,
  FileText,
  ReceiptText,
  UserRound,
  WalletCards,
} from "lucide-react";
import { Reveal } from "./motion";

function AgendaVisual() {
  return (
    <div className="story-visual story-visual--agenda">
      <div className="story-calendar">
        <header><span><CalendarDays /></span><div><small>Agenda clínica</small><strong>Semana atual</strong></div></header>
        <div className="story-calendar__grid">
          {["Seg", "Ter", "Qua", "Qui", "Sex"].map((day, index) => (
            <div key={day}><b>{day}</b><small>{24 + index}</small>{index !== 2 && <span className={index === 3 ? "is-accent" : ""}>Sessão<br /><em>{index % 2 ? "14:00" : "09:00"}</em></span>}</div>
          ))}
        </div>
      </div>
      <div className="story-floating-note"><UserRound /><span><b>Paciente vinculado</b><small>Contexto disponível</small></span></div>
    </div>
  );
}

function RecordsVisual() {
  return (
    <div className="story-visual story-visual--records">
      <div className="story-document story-document--back" />
      <div className="story-document story-document--middle" />
      <article className="story-document story-document--front">
        <header><span><FileText /></span><div><small>Evolução clínica</small><strong>Registro estruturado</strong></div></header>
        <div className="story-document__lines"><span /><span /><span /><span /><span /></div>
        <footer><CheckCircle2 /> Vinculado ao atendimento e ao profissional</footer>
      </article>
      <div className="story-records__tag">Acesso por perfil</div>
    </div>
  );
}

function FinanceVisual() {
  return (
    <div className="story-visual story-visual--finance">
      <div className="story-finance__summary">
        <small>Resumo do período</small>
        <strong>Receitas e pendências</strong>
        <div className="story-finance__chart" aria-hidden="true"><span /><span /><span /><span /><span /><span /><span /></div>
      </div>
      <div className="story-finance__list">
        {["Sessão · Ana Clara", "Sessão · Marcos Lima", "Material clínico"].map((item, index) => (
          <div key={item}><span>{index === 2 ? <ReceiptText /> : <WalletCards />}</span><b>{item}</b><small className={index === 2 ? "is-pending" : ""}>{index === 2 ? "Pendente" : "Pago"}</small></div>
        ))}
      </div>
    </div>
  );
}

export function ModuleStories() {
  return (
    <section id="modulos" className="module-stories">
      <div className="module-stories__intro">
        <span className="landing-eyebrow">Módulos que compartilham contexto</span>
        <h2>Cada área tem sua função. O valor aparece quando elas se conectam.</h2>
      </div>

      <article className="module-story module-story--agenda">
        <Reveal className="module-story__copy">
          <span className="module-story__index">01 · Agenda e pacientes</span>
          <h3>Menos retrabalho entre cadastro e atendimento.</h3>
          <p>A agenda utiliza o contexto do paciente para manter horários, status e informações do atendimento organizados.</p>
          <ul><li><CheckCircle2 />Consultas vinculadas ao paciente correto</li><li><CheckCircle2 />Visualização clara da rotina</li><li><CheckCircle2 />Base para os demais módulos</li></ul>
        </Reveal>
        <Reveal delay={0.08}><AgendaVisual /></Reveal>
      </article>

      <article className="module-story module-story--records">
        <Reveal delay={0.08}><RecordsVisual /></Reveal>
        <Reveal className="module-story__copy">
          <span className="module-story__index">02 · Prontuários</span>
          <h3>Continuidade clínica sem anotações dispersas.</h3>
          <p>As evoluções permanecem relacionadas ao atendimento, ao paciente e ao profissional responsável.</p>
          <ul><li><CheckCircle2 />Histórico clínico centralizado</li><li><CheckCircle2 />Registros relacionados às sessões</li><li><CheckCircle2 />Acesso restrito por responsabilidade</li></ul>
        </Reveal>
      </article>

      <article className="module-story module-story--finance">
        <Reveal className="module-story__copy">
          <span className="module-story__index">03 · Financeiro</span>
          <h3>Visibilidade sobre o que entrou e o que ainda está pendente.</h3>
          <p>Receitas, despesas, vencimentos e pagamentos ficam próximos da operação de atendimento.</p>
          <ul><li><CheckCircle2 />Lançamentos categorizados</li><li><CheckCircle2 />Status e vencimentos visíveis</li><li><CheckCircle2 />Relacionamento com pacientes e consultas</li></ul>
        </Reveal>
        <Reveal delay={0.08}><FinanceVisual /></Reveal>
      </article>
    </section>
  );
}
