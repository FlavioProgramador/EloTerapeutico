"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  CalendarDays,
  CheckCircle2,
  FileText,
  ReceiptText,
  Search,
  ShieldCheck,
  UserRound,
  UsersRound,
  WalletCards,
} from "lucide-react";
import { Reveal } from "./motion";

type ModuleId = "dashboard" | "patients" | "agenda" | "records" | "finance";

interface LandingModule {
  id: ModuleId;
  nome: string;
  beneficio: string;
  descricao: string;
  benefits: string[];
  visual: ModuleId;
}

interface ModuleStoriesProps {
  modules?: LandingModule[];
}

export const landingModules: LandingModule[] = [
  {
    id: "dashboard",
    nome: "Dashboard",
    beneficio: "A rotina inteira em uma leitura rápida.",
    descricao:
      "Visualize compromissos, pacientes, pendências de prontuário e movimentações financeiras sem alternar entre planilhas e anotações soltas.",
    benefits: [
      "Indicadores do período em um só painel",
      "Atividades recentes com contexto operacional",
      "Ações rápidas para os fluxos mais usados",
    ],
    visual: "dashboard",
  },
  {
    id: "patients",
    nome: "Pacientes",
    beneficio: "A base de cuidado organizada desde o cadastro.",
    descricao:
      "Centralize dados cadastrais, contatos e informações essenciais para que agenda, prontuários e financeiro trabalhem sobre o mesmo contexto.",
    benefits: [
      "Cadastro conectado aos demais módulos",
      "Status de acompanhamento sempre visível",
      "Informações administrativas separadas do registro clínico",
    ],
    visual: "patients",
  },
  {
    id: "agenda",
    nome: "Agenda",
    beneficio: "Nunca perca o contexto de um atendimento.",
    descricao:
      "Organize horários, status e vínculos de atendimento para manter a rotina clínica previsível e conectada aos pacientes corretos.",
    benefits: [
      "Consultas vinculadas ao paciente correto",
      "Visualização clara da rotina profissional",
      "Base para financeiro e registros de sessão",
    ],
    visual: "agenda",
  },
  {
    id: "records",
    nome: "Prontuários",
    beneficio: "Evoluções clínicas em um só lugar.",
    descricao:
      "Registre evoluções relacionadas ao atendimento e ao profissional responsável, com uma experiência pensada para continuidade do cuidado.",
    benefits: [
      "Histórico clínico centralizado",
      "Registros relacionados às sessões",
      "Acesso restrito por responsabilidade",
    ],
    visual: "records",
  },
  {
    id: "finance",
    nome: "Financeiro",
    beneficio: "Cobranças e pendências sem planilha paralela.",
    descricao:
      "Acompanhe receitas, despesas, vencimentos e pagamentos próximos da operação de atendimento, sem misturar controles administrativos.",
    benefits: [
      "Lançamentos categorizados por rotina",
      "Status e vencimentos visíveis",
      "Relacionamento com pacientes e consultas",
    ],
    visual: "finance",
  },
];

function DashboardVisual() {
  const metrics = [
    { label: "Atendimentos", value: "23", icon: CalendarDays },
    { label: "Pacientes", value: "Base ativa", icon: UsersRound },
    { label: "Receita", value: "Resumo", icon: WalletCards },
  ];

  return (
    <div className="story-visual story-visual--dashboard">
      <div className="story-dashboard__metrics">
        {metrics.map(({ label, value, icon: Icon }) => (
          <article key={label}>
            <span>
              <Icon aria-hidden="true" />
            </span>
            <small>{label}</small>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
      <div className="story-dashboard__timeline">
        <header>
          <span>
            <Activity aria-hidden="true" />
          </span>
          <div>
            <small>Operação de hoje</small>
            <strong>Visão integrada</strong>
          </div>
        </header>
        {[
          "Sessão confirmada",
          "Pagamento registrado",
          "Prontuário atualizado",
        ].map((item, index) => (
          <div key={item} className={index === 0 ? "is-active" : ""}>
            <span />
            <b>{item}</b>
            <small>{index === 0 ? "Agora" : "Hoje"}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

function PatientsVisual() {
  return (
    <div className="story-visual story-visual--patients">
      <div className="story-patients__directory">
        <header>
          <Search aria-hidden="true" />
          <span>Lista de pacientes</span>
        </header>
        {["Acompanhamento ativo", "Retorno agendado", "Cadastro recente"].map(
          (item, index) => (
            <button
              key={item}
              type="button"
              className={index === 0 ? "is-active" : ""}
            >
              <span>
                <UserRound aria-hidden="true" />
              </span>
              <b>{item}</b>
            </button>
          ),
        )}
      </div>
      <article className="story-patients__profile">
        <header>
          <span>
            <UsersRound aria-hidden="true" />
          </span>
          <div>
            <small>Ficha administrativa</small>
            <strong>Contexto do atendimento</strong>
          </div>
        </header>
        <div className="story-patients__details">
          <span />
          <span />
          <span />
          <span />
        </div>
        <footer>
          <ShieldCheck aria-hidden="true" />
          Dados demonstrativos, sem informações reais.
        </footer>
      </article>
    </div>
  );
}

function AgendaVisual() {
  return (
    <div className="story-visual story-visual--agenda">
      <div className="story-calendar">
        <header>
          <span>
            <CalendarDays aria-hidden="true" />
          </span>
          <div>
            <small>Agenda clínica</small>
            <strong>Semana atual</strong>
          </div>
        </header>
        <div className="story-calendar__grid">
          {["Seg", "Ter", "Qua", "Qui", "Sex"].map((day, index) => (
            <div key={day}>
              <b>{day}</b>
              <small>{24 + index}</small>
              {index !== 2 && (
                <span className={index === 3 ? "is-accent" : ""}>
                  Sessão
                  <br />
                  <em>{index % 2 ? "14:00" : "09:00"}</em>
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="story-floating-note">
        <UserRound aria-hidden="true" />
        <span>
          <b>Paciente vinculado</b>
          <small>Contexto disponível</small>
        </span>
      </div>
    </div>
  );
}

function RecordsVisual() {
  return (
    <div className="story-visual story-visual--records">
      <div className="story-document story-document--back" />
      <div className="story-document story-document--middle" />
      <article className="story-document story-document--front">
        <header>
          <span>
            <FileText aria-hidden="true" />
          </span>
          <div>
            <small>Evolução clínica</small>
            <strong>Registro estruturado</strong>
          </div>
        </header>
        <div className="story-document__lines">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
        <footer>
          <CheckCircle2 aria-hidden="true" /> Vinculado ao atendimento e ao
          profissional
        </footer>
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
        <div className="story-finance__chart" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
      <div className="story-finance__list">
        {["Sessão confirmada", "Retorno registrado", "Material clínico"].map(
          (item, index) => (
            <div key={item}>
              <span>
                {index === 2 ? (
                  <ReceiptText aria-hidden="true" />
                ) : (
                  <WalletCards aria-hidden="true" />
                )}
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

const visuals: Record<ModuleId, () => ReactNode> = {
  dashboard: DashboardVisual,
  patients: PatientsVisual,
  agenda: AgendaVisual,
  records: RecordsVisual,
  finance: FinanceVisual,
};

export function ModuleStories({
  modules = landingModules,
}: ModuleStoriesProps) {
  const moduleList = modules.length > 0 ? modules : landingModules;
  const reduceMotion = useReducedMotion();
  const tablistRef = useRef<HTMLDivElement | null>(null);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const [activeModuleId, setActiveModuleId] = useState<ModuleId>(
    moduleList[0]?.id ?? "dashboard",
  );
  const selectedIndex = Math.max(
    moduleList.findIndex((module) => module.id === activeModuleId),
    0,
  );
  const [focusedIndex, setFocusedIndex] = useState(selectedIndex);
  const [indicator, setIndicator] = useState({
    left: 0,
    width: 0,
    center: 0,
    opacity: 0,
  });
  const active = moduleList[selectedIndex] ?? landingModules[0];
  const ActiveVisual = visuals[active.visual];
  const rovingIndex = moduleList[focusedIndex] ? focusedIndex : selectedIndex;

  useEffect(() => {
    const activeTab = tabRefs.current[selectedIndex];
    const tablist = tablistRef.current;
    if (!activeTab) return;

    const updateIndicator = () => {
      const scrollLeft = tablist?.scrollLeft ?? 0;

      setIndicator({
        left: activeTab.offsetLeft,
        width: activeTab.offsetWidth,
        center: activeTab.offsetLeft - scrollLeft + activeTab.offsetWidth / 2,
        opacity: 1,
      });
    };

    updateIndicator();
    tablist?.addEventListener("scroll", updateIndicator, { passive: true });
    activeTab.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "nearest",
      inline: "center",
    });

    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", updateIndicator);
      return () => {
        window.removeEventListener("resize", updateIndicator);
        tablist?.removeEventListener("scroll", updateIndicator);
      };
    }

    const observer = new ResizeObserver(updateIndicator);
    observer.observe(activeTab);
    if (tablist) observer.observe(tablist);

    return () => {
      observer.disconnect();
      tablist?.removeEventListener("scroll", updateIndicator);
    };
  }, [reduceMotion, selectedIndex]);

  const focusTab = (index: number) => {
    const nextIndex = (index + moduleList.length) % moduleList.length;
    setFocusedIndex(nextIndex);
    tabRefs.current[nextIndex]?.focus();
  };

  const selectTab = (index: number) => {
    const nextModule = moduleList[index];
    if (!nextModule) return;
    setActiveModuleId(nextModule.id);
    setFocusedIndex(index);
  };

  const handleKeyDown = (
    event: ReactKeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      focusTab(index + 1);
      return;
    }

    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      focusTab(index - 1);
      return;
    }

    if (event.key === "Home") {
      event.preventDefault();
      focusTab(0);
      return;
    }

    if (event.key === "End") {
      event.preventDefault();
      focusTab(moduleList.length - 1);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectTab(index);
    }
  };

  return (
    <section id="modulos" className="module-stories-section">
      <div className="module-stories__inner">
        <Reveal className="module-stories__intro">
          <span className="landing-eyebrow">
            Módulos que compartilham contexto
          </span>
          <h2>
            Cada área tem sua função. O valor aparece quando elas se conectam.
          </h2>
        </Reveal>

        <Reveal className="module-selector" delay={0.08}>
          <div
            className="module-tabs"
            role="tablist"
            aria-label="Módulos do Elo Terapêutico"
            ref={tablistRef}
          >
            <span
              className="module-tabs__indicator"
              aria-hidden="true"
              style={{
                opacity: indicator.opacity,
                transform: `translateX(${indicator.left}px)`,
                width: indicator.width,
              }}
            />
            {moduleList.map((module, index) => (
              <button
                key={module.id}
                id={`module-tab-${module.id}`}
                ref={(element) => {
                  tabRefs.current[index] = element;
                }}
                type="button"
                role="tab"
                aria-selected={active.id === module.id}
                aria-controls="module-panel"
                tabIndex={rovingIndex === index ? 0 : -1}
                onClick={() => selectTab(index)}
                onFocus={() => setFocusedIndex(index)}
                onKeyDown={(event) => handleKeyDown(event, index)}
              >
                {module.nome}
              </button>
            ))}
          </div>
          <span
            className="module-selector__connector"
            aria-hidden="true"
            style={{ left: indicator.center, opacity: indicator.opacity }}
          />

          <div className="module-selector__stage">
            <AnimatePresence mode="wait" initial={false}>
              <motion.article
                key={active.id}
                id="module-panel"
                role="tabpanel"
                aria-labelledby={`module-tab-${active.id}`}
                className="module-selector__panel"
                initial={reduceMotion ? false : { opacity: 0, y: 12 }}
                animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              >
                <motion.div
                  className="module-selector__copy"
                  initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                  animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.28,
                    delay: reduceMotion ? 0 : 0.06,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                >
                  <span className="module-story__index">
                    {String(selectedIndex + 1).padStart(2, "0")} · {active.nome}
                  </span>
                  <h3>{active.beneficio}</h3>
                  <p>{active.descricao}</p>
                  <ul>
                    {active.benefits.map((benefit) => (
                      <li key={benefit}>
                        <CheckCircle2 aria-hidden="true" />
                        {benefit}
                      </li>
                    ))}
                  </ul>
                </motion.div>

                <motion.div
                  className="module-selector__screen"
                  aria-label={`Mockup do módulo ${active.nome}`}
                  initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                  animate={reduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                >
                  <div className="module-selector__bar" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                    <small>{active.nome}</small>
                  </div>
                  <ActiveVisual />
                </motion.div>
              </motion.article>
            </AnimatePresence>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
