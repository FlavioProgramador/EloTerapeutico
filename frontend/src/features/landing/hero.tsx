import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Reveal } from "./motion";

export function Hero() {
  const items = ["Agenda integrada", "Prontuário estruturado", "Controle financeiro"];
  return (
    <section id="conteudo" className="landing-hero">
      <div className="landing-hero-copy">
        <Reveal>
          <span className="landing-eyebrow">Gestão para a rotina terapêutica</span>
          <h1>Sua clínica organizada. Seu cuidado no centro.</h1>
          <p>Centralize pacientes, agenda, prontuários e financeiro em uma experiência conectada, clara e preparada para o dia a dia.</p>
          <div className="landing-actions"><Link href="/register">Criar minha conta <ArrowRight /></Link><a href="#produto">Conhecer a plataforma</a></div>
          <div className="landing-checks">{items.map((item) => <span key={item}><CheckCircle2 />{item}</span>)}</div>
        </Reveal>
      </div>
      <Reveal delay={0.08}><div className="landing-hero-preview"><small>VISÃO DEMONSTRATIVA</small><h2>O essencial em uma única tela</h2><div><span>Próximos atendimentos</span><span>Pendências do dia</span><span>Resumo da operação</span></div></div></Reveal>
    </section>
  );
}
