import Link from "next/link";
import { ArrowRight, Play, Calendar, Banknote, Brain, Headset, Shield, Lightbulb, FileText, LayoutList, Library, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

export function NewHero() {
  return (
    <section className="relative min-h-screen flex items-center pt-24 pb-32 overflow-hidden bg-background-dark">
      {/* Background Image & Blending */}
      <div className="absolute inset-0 z-0 bg-[#1A2E26]">
        <img 
          src="/landing_hero.jpg" 
          alt="Terapia Acolhedora" 
          className="w-full h-full object-cover object-[75%_center]"
        />
        {/* Overlay muito sutil apenas para garantir legibilidade, deixando a imagem 100% visível */}
        <div className="absolute inset-0 bg-black/20"></div>
        {/* Gradiente levíssimo apenas atrás do texto */}
        <div className="absolute inset-0 bg-gradient-to-r from-black/50 via-black/20 to-transparent w-full md:w-2/3"></div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 relative z-10">
        <div className="max-w-2xl text-white">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold font-display leading-tight mb-6 text-[#EFF3EE]">
            Atenção Terapêutica <br />
            Que Transforma Vidas
          </h1>
          <p className="text-lg md:text-xl text-[#EFF3EE]/90 mb-10 font-body">
            Oferecemos uma plataforma completa e acolhedora, trazendo conforto, segurança e paz de espírito para você e seus pacientes, do agendamento ao prontuário.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 items-center">
            <Link 
              href="/register" 
              className="group flex items-center justify-between gap-4 bg-primary text-primary-foreground pl-6 pr-2 py-2 rounded-full font-semibold hover:bg-primary-hover transition-colors w-full sm:w-auto"
            >
              Experimente Agora
              <span className="flex items-center justify-center w-9 h-9 rounded-full bg-[#1A2E26] text-white group-hover:scale-105 transition-transform">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
            <a 
              href="#produto" 
              className="flex items-center gap-3 text-white font-medium hover:text-accent transition-colors"
            >
              <span className="flex items-center justify-center w-10 h-10 rounded-full bg-accent text-accent-foreground">
                <Play className="w-4 h-4 fill-current" />
              </span>
              Ver Demonstração
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

export function NewAboutSection() {
  return (
    <section className="py-24 bg-background text-foreground" id="sobre-nos">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div className="max-w-xl">
            <span className="inline-flex items-center gap-2 px-4 py-1.5 border border-border rounded-full text-sm font-medium text-primary mb-8">
              <span className="w-2 h-2 rounded-full bg-accent"></span>
              Sobre Nós
            </span>
            <h2 className="text-4xl md:text-5xl font-display font-bold text-primary mb-6 leading-tight">
              O cuidado psicológico deve ser acessível e organizado para todos
            </h2>
            <p className="text-muted-foreground text-lg mb-10 leading-relaxed font-body">
              O Elo Terapêutico foi fundado com o objetivo de simplificar a rotina clínica de psicólogos e terapeutas. Focamos em entregar segurança de dados, prontuários eficientes e uma gestão descomplicada para que você tenha mais tempo para se dedicar ao que realmente importa: seus pacientes.
            </p>
            
            <Link 
              href="#modulos" 
              className="group inline-flex items-center justify-between gap-4 bg-primary text-primary-foreground pl-6 pr-2 py-2 rounded-full font-semibold hover:bg-primary-hover transition-colors"
            >
              Conhecer mais
              <span className="flex items-center justify-center w-9 h-9 rounded-full bg-[#1A2E26] text-white group-hover:scale-105 transition-transform">
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
          </div>
          <div className="relative">
            <div className="rounded-3xl overflow-hidden shadow-2xl">
              <img 
                src="/landing_about_therapy.png" 
                alt="Sessão de terapia" 
                className="w-full h-auto object-cover aspect-[4/3]"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function NewVideoStatsSection() {
  return (
    <section className="py-24 bg-background text-foreground" id="stats">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="flex flex-col lg:flex-row justify-between items-end mb-12 gap-6">
          <h2 className="text-4xl md:text-5xl font-display font-bold text-primary max-w-2xl leading-tight">
            Veja como a plataforma Elo Terapêutico funciona na prática.
          </h2>
          <p className="text-muted-foreground max-w-md text-lg font-body">
            Oferecemos um sistema seguro, respeitoso e premium, com tecnologia de ponta para a sua clínica.
          </p>
        </div>

        <div className="relative rounded-3xl overflow-hidden shadow-2xl mb-12">
          <img 
            src="/landing_video_thumbnail.png" 
            alt="Demonstração do sistema" 
            className="w-full aspect-video object-cover"
          />
          <button className="absolute bottom-6 left-6 w-12 h-12 flex items-center justify-center rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors backdrop-blur-sm">
            <Play className="w-6 h-6 fill-current" />
          </button>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-primary/5 p-6 rounded-2xl border border-primary/10">
            <div className="text-3xl font-bold text-primary mb-2 font-display">5h+</div>
            <div className="text-sm text-muted-foreground font-medium">Poupadas por semana</div>
          </div>
          <div className="bg-primary/5 p-6 rounded-2xl border border-primary/10">
            <div className="text-3xl font-bold text-primary mb-2 font-display">35.000+</div>
            <div className="text-sm text-muted-foreground font-medium">Sessões registradas</div>
          </div>
          <div className="bg-accent/10 p-6 rounded-2xl border border-accent/20">
            <div className="text-3xl font-bold text-primary mb-2 font-display">100+</div>
            <div className="text-sm text-muted-foreground font-medium">Clínicas ativas</div>
          </div>
          <div className="bg-success/10 p-6 rounded-2xl border border-success/20">
            <div className="text-3xl font-bold text-primary mb-2 font-display">100%</div>
            <div className="text-sm text-muted-foreground font-medium">Adequado à LGPD</div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function NewFeaturesGrid() {
  const features = [
    { title: "Gestão de Agenda", icon: Calendar, text: "Controle seus horários com facilidade." },
    { title: "Financeiro Integrado", icon: Banknote, text: "Receitas, despesas e relatórios em um clique." },
    { title: "Prontuário Especializado", icon: Brain, text: "Evoluções seguras com modelos terapêuticos." },
    { title: "Suporte Dedicado", icon: Headset, text: "Atendimento humano pronto para ajudar." },
    { title: "Conformidade LGPD", icon: Shield, text: "Dados criptografados de ponta a ponta." },
    { title: "Intuitivo e Fácil", icon: Lightbulb, text: "Uma interface amigável para o dia a dia." },
  ];

  return (
    <section className="py-24 bg-surface text-foreground" id="modulos">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-4xl md:text-5xl font-display font-bold text-primary mb-6">Uma Plataforma, Múltiplas Soluções</h2>
          <p className="text-muted-foreground text-lg font-body">
            Ferramentas pensadas para acolhimento e expertise — para que seus atendimentos sejam feitos com segurança, organização e dignidade.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group bg-card border border-border p-6 rounded-2xl hover:border-accent transition-all hover:shadow-lg flex items-center justify-between cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                  <feature.icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-primary font-display">{feature.title}</h3>
                </div>
              </div>
              <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-accent transition-colors" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function NewTailoredCareSection() {
  return (
    <section className="py-24 bg-background text-foreground" id="detalhes">
      <div className="container mx-auto px-4 sm:px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-4xl md:text-5xl font-display font-bold text-primary mb-6">Molde o cuidado com o Elo</h2>
          <p className="text-muted-foreground text-lg font-body">
            A melhor solução em um só lugar para que você tenha todas as ferramentas necessárias para uma gestão clínica impecável.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-1 flex flex-col gap-6">
            <div className="bg-card border border-border p-8 rounded-2xl h-full">
              <LayoutList className="w-8 h-8 text-primary mb-4" />
              <h3 className="text-xl font-bold text-primary mb-3 font-display">Central de Pacientes</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Mantenha todos os detalhes de atendimento em um ambiente seguro. Fique conectado, informado e no controle de sua base de pacientes a qualquer momento.
              </p>
            </div>
            <div className="bg-card border border-border p-8 rounded-2xl h-full">
              <FileText className="w-8 h-8 text-primary mb-4" />
              <h3 className="text-xl font-bold text-primary mb-3 font-display">Plano Terapêutico</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Nossos planos de acompanhamento se adaptam à evolução do paciente. Desenhado cuidadosamente para garantir organização, privacidade e consistência.
              </p>
            </div>
          </div>

          {/* Center Column (Image spans 2 columns) */}
          <div className="lg:col-span-2 rounded-2xl overflow-hidden h-[600px] lg:h-auto">
            <img 
              src="/landing_tailored_care.png" 
              alt="Ambiente Terapêutico" 
              className="w-full h-full object-cover"
            />
          </div>

          {/* Right Column */}
          <div className="lg:col-span-1 flex flex-col gap-6">
            <div className="bg-card border border-border p-8 rounded-2xl h-full">
              <Library className="w-8 h-8 text-primary mb-4" />
              <h3 className="text-xl font-bold text-primary mb-3 font-display">Biblioteca Clínica</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Explore nosso acervo de materiais e escalas validadas. Encontre a ferramenta certa para proporcionar um suporte personalizado e confiável.
              </p>
            </div>
            <div className="bg-card border border-border p-8 rounded-2xl h-full">
              <BookOpen className="w-8 h-8 text-primary mb-4" />
              <h3 className="text-xl font-bold text-primary mb-3 font-display">Diário de Sessões</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Acompanhe o progresso diário, anotações e atividades em um só lugar. Tenha confiança de que as necessidades de cada paciente estão sendo atendidas.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
