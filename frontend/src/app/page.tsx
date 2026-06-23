import React from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  Calendar,
  Users,
  TrendingUp,
  Lock,
  Heart,
  Sparkles,
  Check,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function LandingPage() {
  const features = [
    {
      icon: <Users className="h-6 w-6 text-primary" />,
      title: "CRM de Pacientes",
      description:
        "Fichas completas, histórico de sessões, evolução de diagnósticos e contatos unificados.",
    },
    {
      icon: <Lock className="h-6 w-6 text-teal-500" />,
      title: "Prontuário Criptografado",
      description:
        "Evoluções de sessão com segurança avançada, em estrita conformidade com as regras da LGPD.",
    },
    {
      icon: <Calendar className="h-6 w-6 text-emerald-500" />,
      title: "Agenda Inteligente",
      description:
        "Controle de faltas, presenças, lembretes de sessões e horários integrados com recorrência.",
    },
    {
      icon: <TrendingUp className="h-6 w-6 text-amber-500" />,
      title: "Financeiro & Faturamento",
      description:
        "Fluxo de caixa simplificado, registro automático de receitas por sessão e controle de pendências.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white selection:bg-primary selection:text-white overflow-x-hidden relative">
      {/* Luzes difusas de fundo decorativas */}
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-primary/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-emerald-600/10 blur-[150px] pointer-events-none" />
      <div className="absolute top-[40%] left-[25%] w-[30vw] h-[30vw] rounded-full bg-teal-500/5 blur-[120px] pointer-events-none" />

      {/* Navegação de Topo */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-slate-950/75 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-300">
              Elo Terapêutico
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-300">
            <a href="#features" className="hover:text-white transition-colors">Funcionalidades</a>
            <a href="#security" className="hover:text-white transition-colors">Segurança</a>
            <a href="#pricing" className="hover:text-white transition-colors">Planos</a>
          </nav>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-semibold hover:text-white text-slate-300 transition-colors"
            >
              Entrar
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center justify-center bg-primary text-white font-semibold text-sm h-10 px-5 rounded-lg hover:bg-primary/90 transition-all shadow-md shadow-primary/20 active:scale-97"
            >
              Começar Grátis
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-28 md:pt-32 md:pb-40 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold mb-8 animate-fade-in">
          <Sparkles className="h-3.5 w-3.5" />
          <span>Gestão clínica e prontuários de ponta</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight md:leading-none">
          A evolução na gestão de{" "}
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary via-emerald-400 to-teal-400">
            Consultórios de Psicologia
          </span>
        </h1>
        
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mt-6 leading-relaxed">
          O Elo Terapêutico centraliza prontuários eletrônicos protegidos, controle de agenda
          inteligente e fluxo financeiro em uma única plataforma premium projetada para terapeutas de alto rendimento.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
          <Link
            href="/register"
            className="w-full sm:w-auto inline-flex items-center justify-center bg-primary text-white font-bold text-base h-13 px-8 rounded-lg hover:bg-primary/90 hover:shadow-lg hover:shadow-primary/20 transition-all active:scale-97 group"
          >
            Experimentar agora
            <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a
            href="#features"
            className="w-full sm:w-auto inline-flex items-center justify-center border border-white/10 hover:bg-white/5 text-white font-bold text-base h-13 px-8 rounded-lg transition-all"
          >
            Conhecer recursos
          </a>
        </div>

        {/* Mockup da Interface */}
        <div className="mt-20 relative max-w-5xl mx-auto rounded-2xl border border-white/10 bg-slate-900/50 p-3 backdrop-blur-md shadow-2xl animate-fade-in">
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-primary/5 via-emerald-500/5 to-transparent pointer-events-none" />
          <div className="bg-slate-950 rounded-xl overflow-hidden border border-white/5 aspect-video flex flex-col">
            {/* Topbar do Mockup */}
            <div className="h-10 bg-slate-900/80 border-b border-white/5 flex items-center px-4 gap-1.5 shrink-0">
              <div className="h-3 w-3 rounded-full bg-destructive/60" />
              <div className="h-3 w-3 rounded-full bg-amber-500/60" />
              <div className="h-3 w-3 rounded-full bg-emerald-500/60" />
              <div className="h-5 w-64 bg-slate-950/60 rounded-md mx-auto border border-white/5 flex items-center justify-center text-[10px] text-slate-500">
                app.eloterapeutico.com.br/dashboard
              </div>
            </div>
            {/* Conteúdo do Mockup */}
            <div className="flex-1 flex bg-slate-950 text-left text-xs p-4 gap-4">
              <div className="w-1/4 border-r border-white/5 flex flex-col gap-2 pr-4">
                <div className="h-6 w-3/4 bg-primary/25 rounded-md border border-primary/20" />
                <div className="h-5 w-full bg-white/5 rounded-md" />
                <div className="h-5 w-5/6 bg-white/5 rounded-md" />
                <div className="h-5 w-11/12 bg-white/5 rounded-md" />
              </div>
              <div className="flex-1 flex flex-col gap-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="h-16 bg-white/5 rounded-xl border border-white/5 p-2 flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400">Pacientes Ativos</span>
                    <span className="font-bold text-sm">48</span>
                  </div>
                  <div className="h-16 bg-white/5 rounded-xl border border-white/5 p-2 flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400">Consultas Hoje</span>
                    <span className="font-bold text-sm text-teal-400">8</span>
                  </div>
                  <div className="h-16 bg-white/5 rounded-xl border border-white/5 p-2 flex flex-col justify-between">
                    <span className="text-[10px] text-slate-400">Faturamento Mês</span>
                    <span className="font-bold text-sm text-emerald-400">R$ 12.800</span>
                  </div>
                </div>
                <div className="flex-1 border border-white/5 bg-slate-900/30 rounded-xl p-3 flex flex-col gap-2">
                  <span className="font-bold text-[11px] text-slate-300">Agenda do Dia</span>
                  <div className="h-7 bg-white/5 rounded-lg border border-white/5 flex items-center px-2 justify-between">
                    <span className="font-semibold text-slate-200">Paciente: Amanda Costa</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[9px] border border-emerald-500/20">09:00</span>
                  </div>
                  <div className="h-7 bg-white/5 rounded-lg border border-white/5 flex items-center px-2 justify-between">
                    <span className="font-semibold text-slate-200">Paciente: Roberto Silva</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[9px] border border-emerald-500/20">10:30</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Recursos Chave */}
      <section id="features" className="py-24 border-t border-white/5 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight">
              Tudo o que você precisa em um único lugar
            </h2>
            <p className="text-slate-400 mt-4">
              Desenvolvemos módulos robustos para simplificar a burocracia do seu dia a dia
              e permitir que você foque no que realmente importa: a clínica e seus pacientes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feat, idx) => (
              <Card key={idx} className="bg-slate-900/40 border-white/5 hover:border-primary/20 hover:bg-slate-900/60 transition-all duration-300">
                <CardContent className="p-6 space-y-4">
                  <div className="h-12 w-12 rounded-xl bg-slate-950 flex items-center justify-center border border-white/10">
                    {feat.icon}
                  </div>
                  <h3 className="text-lg font-bold text-white">{feat.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feat.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Seção de Segurança */}
      <section id="security" className="py-24 border-t border-white/5 bg-slate-900/10 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
                <ShieldCheck className="h-4 w-4" />
                <span>Segurança de Ponta</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight leading-tight">
                Privacidade do paciente e proteção jurídica garantida
              </h2>
              <p className="text-slate-400 leading-relaxed">
                Entendemos que o sigilo terapêutico é o pilar mais importante do seu trabalho. 
                Por isso, implementamos criptografia avançada para armazenamento de prontuários, evoluções clínicas e anamneses, garantindo conformidade irrestrita com a LGPD e o CFP.
              </p>
              <div className="space-y-3.5 pt-2">
                {[
                  "Criptografia de dados clínicos em repouso e trânsito",
                  "Backup automatizado em múltiplos servidores",
                  "Termos de confidencialidade e consentimento eletrônico",
                  "Controle de acessos granular com auditoria completa",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="h-5 w-5 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
                      <Check className="h-3.5 w-3.5" />
                    </div>
                    <span className="text-sm font-semibold text-slate-200">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative aspect-square max-w-md mx-auto w-full border border-white/10 rounded-3xl bg-slate-900/50 p-8 flex flex-col justify-center gap-6 overflow-hidden">
              <div className="absolute inset-0 bg-radial from-primary/10 via-transparent to-transparent pointer-events-none animate-pulse" />
              <div className="h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mx-auto">
                <Lock className="h-8 w-8" />
              </div>
              <h3 className="font-bold text-xl text-center text-white">Prontuário Criptografado</h3>
              <p className="text-sm text-center text-slate-400 leading-relaxed">
                As evoluções dos pacientes ficam inacessíveis para terceiros, incluindo nossa equipe de engenharia. Apenas você, por meio de sua chave de login, pode descriptografar os relatórios clínicos.
              </p>
              <div className="h-11 bg-slate-950 border border-white/5 rounded-lg flex items-center justify-center text-xs font-mono text-emerald-500 font-semibold uppercase tracking-wider">
                AES-256 BIT KEY ENCRYPTION ACTIVE
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-slate-950 relative z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Activity className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-base tracking-tight text-white">
              Elo Terapêutico
            </span>
          </div>

          <p className="text-xs text-slate-500 text-center md:text-left">
            &copy; {new Date().getFullYear()} Elo Terapêutico. Todos os direitos reservados.
            Em conformidade com a LGPD e regulamentações do Conselho Federal de Psicologia.
          </p>

          <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
            <span>Desenvolvido com carinho para</span>
            <Heart className="h-3.5 w-3.5 text-primary fill-primary animate-pulse" />
            <span>psicólogos</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
