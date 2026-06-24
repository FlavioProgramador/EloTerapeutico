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
  Star,
  ArrowRight,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  const benefits = [
    {
      icon: (
        <div className="h-8 w-8 rounded-full bg-[hsl(165,40%,12%)]/10 flex items-center justify-center text-[hsl(165,40%,12%)] shrink-0">
          <Lock className="h-4 w-4" />
        </div>
      ),
      title: "Tudo em um só lugar",
      description: "Agenda, prontuários, finanças, pacientes e muito mais.",
    },
    {
      icon: (
        <div className="h-8 w-8 rounded-full bg-[hsl(165,40%,12%)]/10 flex items-center justify-center text-[hsl(165,40%,12%)] shrink-0">
          <TrendingUp className="h-4 w-4" />
        </div>
      ),
      title: "Mais tempo para o que importa",
      description: "Automatize tarefas e ganhe horas no seu dia.",
    },
    {
      icon: (
        <div className="h-8 w-8 rounded-full bg-[hsl(165,40%,12%)]/10 flex items-center justify-center text-[hsl(165,40%,12%)] shrink-0">
          <ShieldCheck className="h-4 w-4" />
        </div>
      ),
      title: "Seguro e confiável",
      description: "Seus dados protegidos com criptografia de ponta.",
    },
    {
      icon: (
        <div className="h-8 w-8 rounded-full bg-[hsl(165,40%,12%)]/10 flex items-center justify-center text-[hsl(165,40%,12%)] shrink-0">
          <Users className="h-4 w-4" />
        </div>
      ),
      title: "Feito por terapeutas",
      description: "Criado para a realidade de quem cuida de pessoas.",
    },
  ];

  const testimonials = [
    {
      stars: 5,
      text: "O Elo mudou minha rotina. Hoje tenho mais organização e menos estresse.",
      name: "Juliana Martins",
      role: "Psicóloga",
      initials: "JM",
    },
    {
      stars: 5,
      text: "Prático, bonito e completo. Finalmente um sistema feito para terapeutas de verdade.",
      name: "Rafael Souza",
      role: "Terapeuta Sistêmico",
      initials: "RS",
    },
    {
      stars: 5,
      text: "Minha agenda, meus atendimentos e minhas finanças, tudo integrado e fácil de usar.",
      name: "Camila Ferreira",
      role: "Psicopedagoga",
      initials: "CF",
    },
  ];

  return (
    <div className="min-h-screen bg-[hsl(165,40%,7%)] text-[hsl(40,20%,94%)] selection:bg-[hsl(38,25%,87%)] selection:text-[hsl(165,40%,7%)] font-sans antialiased">
      
      {/* Barra de Navegação */}
      <header className="sticky top-0 z-50 bg-[hsl(165,40%,7%)]/90 backdrop-blur-md border-b border-[hsl(165,27%,16%)]">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-[hsl(38,25%,87%)]/10 flex items-center justify-center text-[hsl(38,25%,87%)]">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="font-bold text-xl tracking-tight text-[hsl(40,20%,94%)]">
              Elo Terapêutico
            </span>
          </div>

          {/* Menu Horizontal */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-[hsl(163,8%,68%)]">
            <a href="#features" className="hover:text-[hsl(40,20%,94%)] transition-colors">Recursos</a>
            <a href="#benefits" className="hover:text-[hsl(40,20%,94%)] transition-colors">Funcionalidades</a>
            <a href="#testimonials" className="hover:text-[hsl(40,20%,94%)] transition-colors">Para quem</a>
            <a href="#testimonials" className="hover:text-[hsl(40,20%,94%)] transition-colors">Depoimentos</a>
            <a href="#pricing" className="hover:text-[hsl(40,20%,94%)] transition-colors">Preços</a>
          </nav>

          <div className="flex items-center gap-5">
            <Link
              href="/login"
              className="text-sm font-semibold hover:text-[hsl(40,20%,94%)] text-[hsl(163,8%,68%)] transition-colors"
            >
              Entrar
            </Link>
            <Link href="/register">
              <Button className="bg-[hsl(38,25%,87%)] hover:bg-[hsl(38,22%,83%)] text-[hsl(165,40%,7%)] font-bold rounded-full px-5 py-5 text-sm flex items-center gap-1.5 transition-all">
                Começar agora <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-20 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <div className="lg:col-span-7 space-y-6 text-left">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[hsl(165,27%,12%)] border border-[hsl(165,27%,16%)] text-[hsl(163,27%,62%)] text-xs font-bold uppercase tracking-wider">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>O sistema feito para terapeutas</span>
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-[1.1] text-[hsl(40,20%,94%)] font-sans">
            Gestão completa.<br />
            Mais tempo para <span className="text-[hsl(163,27%,62%)] font-serif italic font-normal">cuidar.</span>
          </h1>
          
          <p className="text-base md:text-lg text-[hsl(163,8%,68%)] max-w-xl leading-relaxed">
            Organize sua agenda, prontuários, finanças e pacientes em um só lugar. Menos burocracia, mais propósito.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 pt-2">
            <Link href="/register" className="w-full sm:w-auto">
              <Button className="w-full sm:w-auto bg-[hsl(38,25%,87%)] hover:bg-[hsl(38,22%,83%)] text-[hsl(165,40%,7%)] font-bold text-sm rounded-full px-8 py-6 flex items-center justify-center gap-2 transition-all">
                Começar agora
              </Button>
            </Link>
            <a href="#features" className="w-full sm:w-auto">
              <Button variant="outline" className="w-full sm:w-auto border-[hsl(165,27%,16%)] hover:bg-[hsl(165,27%,12%)] text-[hsl(40,20%,94%)] font-bold text-sm rounded-full px-8 py-6 flex items-center justify-center">
                Ver funcionalidades
              </Button>
            </a>
          </div>

          <div className="flex items-center gap-6 pt-4 text-xs text-[hsl(163,8%,68%)]">
            <div className="flex items-center gap-1.5">
              <Check className="h-4 w-4 text-[hsl(163,27%,62%)]" />
              <span>Teste grátis por 14 dias</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Check className="h-4 w-4 text-[hsl(163,27%,62%)]" />
              <span>Cancelamento fácil</span>
            </div>
          </div>
        </div>

        {/* Hero Imagem */}
        <div className="lg:col-span-5 relative flex justify-center lg:justify-end">
          <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-[hsl(165,27%,16%)] max-w-[400px] w-full aspect-[4/5] bg-[hsl(165,38%,10%)]">
            <img 
              src="/terapeuta_acolhedora.png" 
              alt="Terapeuta acolhedora sorrindo no consultório"
              className="w-full h-full object-cover grayscale-[15%] contrast-[105%]"
            />
            {/* Cartão flutuante */}
            <div className="absolute bottom-6 left-6 right-6 p-4 rounded-xl glass-effect border border-white/10 flex items-center gap-3 animate-fade-in shadow-lg">
              <div className="h-10 w-10 rounded-lg bg-[hsl(163,27%,62%)]/20 flex items-center justify-center text-[hsl(163,27%,62%)] shrink-0">
                <Calendar className="h-5 w-5" />
              </div>
              <div className="text-left">
                <p className="text-xs font-bold text-[hsl(40,20%,94%)]">Sua agenda organizada</p>
                <p className="text-[10px] text-[hsl(163,8%,68%)]">+ produtividade no dia a dia</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Seção Benefícios (Faixa Clara) */}
      <section id="benefits" className="bg-[hsl(38,25%,97%)] text-[hsl(165,40%,7%)] py-16 border-y border-[hsl(38,20%,90%)]">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {benefits.map((benefit, idx) => (
            <div key={idx} className="bg-[hsl(38,25%,94%)]/50 border border-[hsl(38,20%,88%)] rounded-xl p-5 shadow-xs transition-all hover:translate-y-[-2px] hover:shadow-sm duration-300 flex flex-col gap-4 text-left">
              {benefit.icon}
              <div className="space-y-1">
                <h4 className="font-bold text-sm text-[hsl(165,40%,12%)]">{benefit.title}</h4>
                <p className="text-xs text-[hsl(165,15%,45%)] leading-relaxed">{benefit.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Depoimentos ("Quem usa, recomenda") */}
      <section id="testimonials" className="py-20 border-b border-[hsl(165,27%,16%)] bg-[hsl(165,40%,7%)]">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-normal tracking-tight font-serif italic text-[hsl(40,20%,94%)] mb-12">
            Quem usa, recomenda
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {testimonials.map((test, idx) => (
              <div 
                key={idx} 
                className="bg-[hsl(165,38%,10%)] border border-[hsl(165,27%,16%)] rounded-xl p-6 flex flex-col justify-between hover:border-[hsl(163,27%,62%)]/30 transition-all duration-300"
              >
                <div className="space-y-4">
                  {/* Estrelas */}
                  <div className="flex gap-1 text-[hsl(38,25%,87%)]">
                    {Array.from({ length: test.stars }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-current" />
                    ))}
                  </div>
                  <p className="text-sm text-[hsl(163,8%,68%)] leading-relaxed">
                    "{test.text}"
                  </p>
                </div>

                <div className="flex items-center gap-3 pt-6 border-t border-[hsl(165,27%,16%)]/40 mt-6">
                  <div className="h-9 w-9 rounded-full bg-[hsl(38,25%,87%)]/10 flex items-center justify-center text-[hsl(38,25%,87%)] font-bold text-xs">
                    {test.initials}
                  </div>
                  <div>
                    <h5 className="font-bold text-xs text-[hsl(40,20%,94%)]">{test.name}</h5>
                    <p className="text-[10px] text-[hsl(163,8%,68%)]">{test.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Chamada Final (CTA Faixa Clara) */}
      <section className="bg-[hsl(38,25%,97%)] text-[hsl(165,40%,7%)] py-14 overflow-hidden relative">
        <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row md:items-center justify-between gap-8 text-left relative z-10">
          <div className="flex items-center gap-6">
            {/* Ilustração de Folha Sutil da Referência */}
            <div className="hidden md:block shrink-0 text-[hsl(165,30%,40%)]/30">
              <svg className="h-16 w-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 22C12 22 17 12 17 2" />
                <path d="M9 14c0-3.5 2.5-6 5.5-6" />
                <path d="M5 18c0-3.5 2-5.5 4.5-5.5" />
                <path d="M13 10c0-3.5 2.5-5 4-5" />
                <path d="M17 2c2 1.5 3 3.5 3 5.5s-1.5 3.5-3 4" />
                <path d="M13.5 8c1.5 1 2.5 2.5 2.5 4s-1 2.5-2 3" />
                <path d="M9.5 12.5c1.5 1 2 2 2 3s-.5 2-1.5 2.5" />
              </svg>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-2xl md:text-3xl font-bold font-sans text-[hsl(165,40%,12%)] leading-tight">
                Pronto para transformar sua rotina?
              </h3>
              <p className="text-sm text-[hsl(165,15%,45%)]">
                Teste grátis por 14 dias. Sem compromisso.
              </p>
            </div>
          </div>

          <Link href="/register" className="shrink-0">
            <Button className="bg-[hsl(165,40%,7%)] hover:bg-[hsl(165,40%,12%)] text-[hsl(40,20%,94%)] font-bold text-sm rounded-full px-8 py-6 flex items-center gap-2 transition-all">
              Começar agora <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Rodapé Redesenhado */}
      <footer className="border-t border-[hsl(165,27%,16%)] bg-[hsl(165,40%,7%)] pt-16 pb-12 text-xs">
        <div className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-12 gap-8 pb-12 border-b border-[hsl(165,27%,16%)]/40">
          
          {/* Logo e Descrição */}
          <div className="md:col-span-4 space-y-4 text-left">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-[hsl(38,25%,87%)]/10 flex items-center justify-center text-[hsl(38,25%,87%)]">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
              </div>
              <span className="font-bold text-lg text-[hsl(40,20%,94%)]">Elo Terapêutico</span>
            </div>
            <p className="text-[11px] text-[hsl(163,8%,68%)] leading-relaxed max-w-xs">
              Sistema completo de gestão para terapeutas que querem mais tempo para cuidar. Conforme LGPD e resoluções do CFP.
            </p>
          </div>

          {/* Colunas de Links */}
          <div className="md:col-span-2 space-y-3 text-left">
            <h5 className="font-bold text-[hsl(40,20%,94%)]">Produto</h5>
            <ul className="space-y-2 text-[hsl(163,8%,68%)]">
              <li><a href="#features" className="hover:text-[hsl(40,20%,94%)] transition-colors">Recursos</a></li>
              <li><a href="#benefits" className="hover:text-[hsl(40,20%,94%)] transition-colors">Funcionalidades</a></li>
              <li><a href="#pricing" className="hover:text-[hsl(40,20%,94%)] transition-colors">Preços</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Novidades</a></li>
            </ul>
          </div>

          <div className="md:col-span-2 space-y-3 text-left">
            <h5 className="font-bold text-[hsl(40,20%,94%)]">Empresa</h5>
            <ul className="space-y-2 text-[hsl(163,8%,68%)]">
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Sobre nós</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Blog</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Carreiras</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Contato</a></li>
            </ul>
          </div>

          <div className="md:col-span-2 space-y-3 text-left">
            <h5 className="font-bold text-[hsl(40,20%,94%)]">Suporte</h5>
            <ul className="space-y-2 text-[hsl(163,8%,68%)]">
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Central de ajuda</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Privacidade</a></li>
              <li><a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Termos de uso</a></li>
            </ul>
          </div>

          {/* Receba Novidades */}
          <div className="md:col-span-2 space-y-3 text-left">
            <h5 className="font-bold text-[hsl(40,20%,94%)]">Receba novidades</h5>
            <div className="flex gap-2">
              <input 
                type="email" 
                placeholder="Seu melhor e-mail" 
                className="w-full bg-[hsl(165,27%,12%)] border border-[hsl(165,27%,16%)] rounded-lg px-3 py-2 text-[11px] text-[hsl(40,20%,94%)] placeholder:text-[hsl(163,8%,68%)]/50 focus:outline-none focus:border-[hsl(38,25%,87%)] transition-colors"
              />
              <button className="bg-[hsl(165,27%,12%)] hover:bg-[hsl(165,27%,16%)] border border-[hsl(165,27%,16%)] rounded-lg px-3 flex items-center justify-center text-[hsl(38,25%,87%)] transition-colors">
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Rodapé base com ilustração */}
        <div className="max-w-6xl mx-auto px-6 pt-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3 text-[hsl(163,8%,68%)]">
            {/* Ilustração Folha Sutil */}
            <svg className="h-5 w-5 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M12 8a3 3 0 00-3 3v4a3 3 0 006 0v-4a3 3 0 00-3-3z" />
            </svg>
            <span>&copy; {new Date().getFullYear()} Elo Terapêutico. Todos os direitos reservados.</span>
          </div>

          <div className="flex items-center gap-4 text-[hsl(163,8%,68%)]">
            <a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">LinkedIn</a>
            <a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Instagram</a>
            <a href="#" className="hover:text-[hsl(40,20%,94%)] transition-colors">Contato</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
