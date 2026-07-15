"use client";

import { useState } from "react";
import {
  Activity,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  Search,
  Users,
  WalletCards,
  type LucideIcon,
} from "lucide-react";
import { productTabs, type ProductTabId } from "./content";
import { Reveal } from "./motion";

const overviewMetrics: Array<{
  label: string;
  value: string;
  icon: LucideIcon;
}> = [
  { label: "Atendimentos", value: "23", icon: CalendarDays },
  { label: "Pacientes", value: "Base ativa", icon: Users },
  { label: "Receita", value: "R$ 8.540", icon: WalletCards },
  { label: "Pendências", value: "2 ações", icon: Activity },
];

function OverviewPanel() {
  return (
    <div className="product-ui__overview">
      <div className="product-ui__metrics">
        {overviewMetrics.map(({ label, value, icon: Icon }) => (
          <article key={label}>
            <span>
              <Icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <small>{label}</small>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
      <div className="product-ui__columns">
        <section>
          <header>
            <strong>Agenda de hoje</strong>
            <small>Visual demonstrativo</small>
          </header>
          {[
            "08:00 · Ana Clara",
            "09:30 · Marcos Lima",
            "11:00 · Juliana Rocha",
          ].map((item) => (
            <div key={item} className="product-ui__row">
              <Clock3 aria-hidden="true" />
              <span>{item}</span>
              <b>Confirmado</b>
            </div>
          ))}
        </section>
        <section>
          <header>
            <strong>Atividades recentes</strong>
            <small>Atualizações do sistema</small>
          </header>
          {[
            "Paciente cadastrado",
            "Pagamento registrado",
            "Prontuário atualizado",
          ].map((item) => (
            <div key={item} className="product-ui__activity">
              <span />
              <b>{item}</b>
              <small>Agora</small>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}

function AgendaPanel() {
  return (
    <div className="product-ui__agenda">
      <div className="product-ui__calendar-head">
        <div>
          <small>Agenda clínica</small>
          <strong>Semana atual</strong>
        </div>
        <button type="button">Novo atendimento</button>
      </div>
      <div className="product-ui__week">
        {["Seg", "Ter", "Qua", "Qui", "Sex"].map((day, dayIndex) => (
          <div key={day} className="product-ui__day">
            <strong>{day}</strong>
            <small>{24 + dayIndex}</small>
            {dayIndex !== 2 && (
              <span className={dayIndex === 3 ? "is-accent" : ""}>
                <b>{dayIndex % 2 ? "14:00" : "09:00"}</b>
                Sessão
              </span>
            )}
          </div>
        ))}
      </div>
      <div className="product-ui__agenda-foot">
        <CheckCircle2 aria-hidden="true" /> Horários, paciente e status
        permanecem no mesmo fluxo.
      </div>
    </div>
  );
}

function RecordsPanel() {
  return (
    <div className="product-ui__records">
      <aside>
        <Search aria-hidden="true" />
        <span>Histórico clínico</span>
        {["Sessão 12", "Sessão 11", "Sessão 10"].map((item, index) => (
          <button
            key={item}
            type="button"
            className={index === 0 ? "is-active" : ""}
          >
            {item}
          </button>
        ))}
      </aside>
      <article>
        <header>
          <span>
            <FileText aria-hidden="true" />
          </span>
          <div>
            <small>Evolução clínica</small>
            <strong>Atendimento vinculado</strong>
          </div>
        </header>
        <div className="product-ui__record-lines">
          <span />
          <span />
          <span />
          <span />
        </div>
        <footer>
          <CheckCircle2 aria-hidden="true" /> Registro associado ao paciente e
          ao profissional responsável.
        </footer>
      </article>
    </div>
  );
}

function FinancePanel() {
  return (
    <div className="product-ui__finance">
      <div className="product-ui__finance-summary">
        <small>Resumo financeiro</small>
        <strong>Visão do período</strong>
        <div className="product-ui__chart" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="product-ui__transactions">
        {["Sessão · Ana Clara", "Sessão · Marcos Lima", "Material clínico"].map(
          (item, index) => (
            <div key={item}>
              <span>
                <WalletCards aria-hidden="true" />
              </span>
              <b>{item}</b>
              <small className={index === 2 ? "is-pending" : ""}>
                {index === 2 ? "Pendente" : "Pago"}
              </small>
            </div>
          ),
        )}
      </div>
    </div>
  );
}

export function ProductStage() {
  const [activeTab, setActiveTab] = useState<ProductTabId>("overview");
  const active =
    productTabs.find((item) => item.id === activeTab) ?? productTabs[0];

  return (
    <section id="produto" className="product-stage">
      <div className="product-stage__inner">
        <Reveal className="product-stage__heading">
          <span className="landing-eyebrow">O produto em funcionamento</span>
          <h2>Uma interface que mostra a operação, não apenas recursos.</h2>
          <p>{active.description}</p>
        </Reveal>

        <Reveal className="product-stage__frame" delay={0.08}>
          <div
            className="product-stage__tabs"
            role="tablist"
            aria-label="Áreas da plataforma"
          >
            {productTabs.map((tab) => (
              <button
                key={tab.id}
                id={`product-tab-${tab.id}`}
                type="button"
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls="product-panel"
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="product-stage__browser">
            <div className="product-stage__bar">
              <span />
              <span />
              <span />
              <small>Dados demonstrativos</small>
            </div>
            <div
              id="product-panel"
              role="tabpanel"
              aria-labelledby={`product-tab-${activeTab}`}
              className="product-stage__canvas"
            >
              {activeTab === "overview" && <OverviewPanel />}
              {activeTab === "agenda" && <AgendaPanel />}
              {activeTab === "records" && <RecordsPanel />}
              {activeTab === "finance" && <FinancePanel />}
            </div>
          </div>
          <div className="product-stage__caption">
            <strong>{active.title}</strong>
            <span>{active.eyebrow}</span>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
