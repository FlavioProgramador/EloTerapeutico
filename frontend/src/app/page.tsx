"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Calendar,
  Users,
  TrendingUp,
  Lock,
  Check,
  ShieldAlert,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const features = [
    {
      icon: <Users className="h-5 w-5 text-primary" />,
      title: "CRM de Pacientes",
      description:
        "Fichas cadastrais limpas, contatos rápidos e detecção de menoridade para termos de consentimento.",
    },
    {
      icon: <Lock className="h-5 w-5 text-primary" />,
      title: "Prontuário Criptografado",
      description:
        "Evoluções em conformidade com a LGPD e auto-bloqueio de edição de 48h (normativa do CFP).",
    },
    {
      icon: <Calendar className="h-5 w-5 text-primary" />,
      title: "Agenda com Validação",
      description:
        "Grade de expediente integrada com busca em tempo real de horários livres e recorrências.",
    },
    {
      icon: <TrendingUp className="h-5 w-5 text-primary" />,
      title: "Fluxo Financeiro",
      description:
        "Geração de receitas automáticas a partir de consultas confirmadas e controle simples de pendências.",
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground selection:bg-primary selection:text-primary-foreground font-sans">
      
      {/* Barra de Navegação */}
      <header className="border-b border-border/80 sticky top-0 z-50 bg-background/95 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-md bg-primary flex items-center justify-center">
              <Lock className="h-4.5 w-4.5 text-primary-foreground" />
            </div>
            <span className="font-bold text-lg tracking-tight text-foreground font-sans">
              Elo Terapêutico
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-semibold hover:text-primary text-muted-foreground transition-colors"
            >
              Entrar
            </Link>
            <Link href="/register">
              <Button size="sm" className="font-semibold text-white">
                Começar Grátis
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 text-center">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary text-primary text-xs font-bold mb-6">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Gestão clínica ética em conformidade com a LGPD</span>
        </div>
        
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight max-w-3xl mx-auto leading-tight text-foreground">
          Gestão clínica descomplicada. <br />
          <span className="text-primary">Prontuários protegidos.</span>
        </h1>
        
        <p className="text-base md:text-lg text-muted-foreground max-w-xl mx-auto mt-6 leading-relaxed">
          Centralize evoluções clínicas criptografadas, controle de agenda inteligente e conciliação financeira em um ambiente calmo e seguro projetado para terapeutas.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-8">
          <Link href="/register" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto font-bold text-white px-6">
              Começar Teste de 14 Dias
            </Button>
          </Link>
          <a href="#features" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto border-border text-foreground px-6">
              Conhecer Recursos
            </Button>
          </a>
        </div>

        {/* Mockup Realista da Interface */}
        <div className="mt-14 max-w-4xl mx-auto rounded-lg border border-border/80 bg-card p-2 shadow-sm">
          <div className="rounded-md overflow-hidden border border-border/50 aspect-video flex flex-col bg-background text-left text-xs select-none">
            {/* Topbar do Mockup */}
            <div className="h-9 bg-secondary/80 border-b border-border/50 flex items-center px-4 gap-1.5 shrink-0">
              <div className="h-2.5 w-2.5 rounded-full bg-border/80" />
              <div className="h-2.5 w-2.5 rounded-full bg-border/80" />
              <div className="h-2.5 w-2.5 rounded-full bg-border/80" />
              <div className="h-5 w-72 bg-card rounded-md mx-auto border border-border/40 flex items-center justify-center text-[10px] text-muted-foreground/80 font-mono">
                app.eloterapeutico.com.br/dashboard
              </div>
            </div>
            {/* Corpo do Mockup */}
            <div className="flex-1 flex text-xs p-4 gap-4 bg-background">
              {/* Sidebar do Mockup */}
              <div className="w-1/4 border-r border-border/40 flex flex-col gap-2.5 pr-4">
                <div className="h-6 w-3/4 bg-primary/20 rounded-md border border-primary/20" />
                <div className="h-5 w-full bg-secondary/40 rounded-md" />
                <div className="h-5 w-5/6 bg-secondary/40 rounded-md" />
                <div className="h-5 w-11/12 bg-secondary/40 rounded-md" />
              </div>
              {/* Painel do Mockup */}
              <div className="flex-1 flex flex-col gap-4">
                <div className="grid grid-cols-4 gap-3">
                  <div className="h-14 bg-card rounded-lg border border-border/80 p-2 flex flex-col justify-between">
                    <span className="text-[9px] text-muted-foreground uppercase font-bold">Ocupação</span>
                    <span className="font-bold text-sm text-foreground">72%</span>
                  </div>
                  <div className="h-14 bg-card rounded-lg border border-border/80 p-2 flex flex-col justify-between">
                    <span className="text-[9px] text-muted-foreground uppercase font-bold">Pendentes</span>
                    <span className="font-bold text-sm text-primary">3</span>
                  </div>
                  <div className="h-14 bg-card rounded-lg border border-border/80 p-2 flex flex-col justify-between">
                    <span className="text-[9px] text-muted-foreground uppercase font-bold">Faturado</span>
                    <span className="font-bold text-sm text-foreground">R$ 6.200</span>
                  </div>
                  <div className="h-14 bg-card rounded-lg border border-border/80 p-2 flex flex-col justify-between">
                    <span className="text-[9px] text-muted-foreground uppercase font-bold">Abstenção</span>
                    <span className="font-bold text-sm text-foreground">5%</span>
                  </div>
                </div>
                <div className="flex-1 border border-border/60 bg-card rounded-lg p-3 flex flex-col gap-2">
                  <span className="font-bold text-[10px] text-foreground uppercase tracking-wider">Agenda de Hoje</span>
                  <div className="h-8 bg-secondary/30 rounded-md border border-border/30 flex items-center px-2 justify-between">
                    <span className="font-semibold text-foreground">Amanda Costa</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 text-[9px] border border-emerald-500/20">09:00 - Confirmada</span>
                  </div>
                  <div className="h-8 bg-secondary/30 rounded-md border border-border/30 flex items-center px-2 justify-between">
                    <span className="font-semibold text-foreground">Roberto Silva</span>
                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[9px] border border-primary/20">10:30 - Agendada</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Grid de Funcionalidades */}
      <section id="features" className="py-20 border-t border-border/80 bg-secondary/10">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center max-w-xl mx-auto mb-14">
            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
              Tudo o que você precisa em um único lugar
            </h2>
            <p className="text-muted-foreground mt-3 text-sm leading-relaxed">
              Elimine a burocracia do expediente clínico. Criamos módulos integrados e focados em salvar o seu tempo operacional.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feat, idx) => (
              <Card key={idx} className="border-border/50 bg-card">
                <CardContent className="p-6 flex items-start gap-4">
                  <div className="h-10 w-10 rounded-md bg-secondary flex items-center justify-center shrink-0 border border-border/55">
                    {feat.icon}
                  </div>
                  <div className="space-y-1.5">
                    <h3 className="text-base font-bold text-foreground">{feat.title}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{feat.description}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Segurança */}
      <section id="security" className="py-20 border-t border-border/80">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
            <div className="space-y-5">
              <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold">
                <ShieldCheck className="h-4 w-4" />
                <span>Segurança CFP / LGPD</span>
              </div>
              <h2 className="text-2xl md:text-4xl font-extrabold tracking-tight text-foreground">
                Prontuários blindados e sigilo profissional
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                As evoluções dos seus pacientes são criptografadas ponta a ponta em repouso no servidor. Apenas sua conta autenticada tem acesso à descriptografia das anotações das sessões.
              </p>
              <div className="space-y-2 pt-2">
                {[
                  "Criptografia simétrica em repouso (AES-128-CBC via Fernet)",
                  "Auto-bloqueio de registros de prontuários após 48h",
                  "Logs de auditoria transparentes para leitura",
                  "Backup contínuo de dados de saúde na nuvem",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-600 shrink-0">
                      <Check className="h-3 w-3" />
                    </div>
                    <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-border/80 rounded-xl bg-card p-6 flex flex-col justify-center gap-4 max-w-sm mx-auto w-full">
              <div className="h-12 w-12 rounded-md bg-secondary flex items-center justify-center text-primary border border-border/40 mx-auto">
                <ShieldAlert className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-base text-center text-foreground">Criptografia Ativa</h3>
              <p className="text-xs text-center text-muted-foreground leading-relaxed">
                Seus dados clínicos de saúde sensíveis (Art. 11 LGPD) são guardados de forma segura sob chaves criptográficas exclusivas.
              </p>
              <div className="h-9 bg-secondary border border-border/30 rounded-md flex items-center justify-center text-[10px] font-mono text-primary font-bold uppercase tracking-wider">
                AES-128 KEY ENCRYPTION STANDARD
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Preços */}
      <section id="pricing" className="py-20 border-t border-border/80 bg-secondary/15 text-center">
        <div className="max-w-md mx-auto px-6 space-y-6">
          <h2 className="text-2xl md:text-3xl font-extrabold text-foreground">Um único plano. Acesso ilimitado.</h2>
          <p className="text-sm text-muted-foreground">
            Esqueça limites artificiais de quantidade de pacientes cadastrados ou de prontuários.
          </p>
          <Card className="border-border/80 bg-card p-6 space-y-4">
            <h3 className="text-lg font-bold">Plano Terapêutico</h3>
            <div className="flex items-baseline justify-center gap-1 font-mono">
              <span className="text-xl text-muted-foreground font-semibold">R$</span>
              <span className="text-4xl font-extrabold text-foreground">79</span>
              <span className="text-sm text-muted-foreground">/mês</span>
            </div>
            <p className="text-xs text-muted-foreground">14 dias de teste grátis. Não requer cartão de crédito.</p>
            <Link href="/register" className="block">
              <Button className="w-full text-white font-bold">Experimentar Grátis</Button>
            </Link>
          </Card>
        </div>
      </section>

      {/* Rodapé */}
      <footer className="border-t border-border/80 py-10 bg-background text-xs">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-primary flex items-center justify-center">
              <Lock className="h-3.5 w-3.5 text-primary-foreground" />
            </div>
            <span className="font-bold text-foreground">Elo Terapêutico</span>
          </div>

          <p className="text-muted-foreground/80 text-center sm:text-left">
            &copy; {new Date().getFullYear()} Elo Terapêutico. Conforme LGPD e resoluções do CFP.
          </p>
        </div>
      </footer>
    </div>
  );
}
