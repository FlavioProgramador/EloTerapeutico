"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { Brand } from "./brand";
import { cn } from "@/lib/utils";

const links = [
  ["Produto", "#produto"],
  ["Como funciona", "#fluxo"],
  ["Módulos", "#modulos"],
  ["Segurança", "#seguranca"],
  ["Perguntas", "#faq"],
] as const;

export function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 w-full z-50 transition-all duration-300",
      scrolled ? "pt-2" : "pt-6"
    )}>
      <a href="#conteudo" className="sr-only focus:not-sr-only">Pular para o conteúdo</a>

      <div className="container mx-auto px-4 sm:px-6">
        <div className={cn(
          "flex items-center justify-between px-3 py-2.5 rounded-full transition-all duration-300 backdrop-blur-md",
          scrolled ? "bg-black/60 shadow-lg" : "bg-black/30 shadow-md"
        )}>
          {/* Brand */}
          <div className="flex-shrink-0 pl-3 [&_span]:!text-[#F97316] [&_.grid]:!bg-transparent [&_.grid]:!border-transparent [&_.grid]:!text-[#F97316] [&_svg]:!w-7 [&_svg]:!h-7">
            <Brand compact />
          </div>

          {/* Desktop Nav */}
          <nav aria-label="Navegação principal" className="hidden lg:flex items-center gap-8 text-sm font-medium text-white/90">
            {links.map(([label, href]) => (
              <a key={href} href={href} className="hover:text-white transition-colors">
                {label}
              </a>
            ))}
          </nav>

          {/* Actions */}
          <div className="hidden lg:flex items-center gap-4 pr-1">
            <Link href="/login" className="text-sm font-medium text-white hover:text-white/80 transition-colors">
              Entrar
            </Link>
            <Link
              href="/register"
              className="group flex items-center justify-between gap-3 bg-[#F97316] text-white pl-5 pr-1.5 py-1.5 rounded-full text-sm font-bold hover:bg-[#EA580C] transition-all shadow-lg"
            >
              Cadastre-se
              <span className="flex items-center justify-center w-7 h-7 rounded-full bg-[#1A2E26] group-hover:scale-105 transition-transform">
                <ArrowRight className="w-3.5 h-3.5 text-white" />
              </span>
            </Link>
          </div>

          {/* Mobile menu toggle */}
          <button
            type="button"
            className="lg:hidden p-2 text-white hover:bg-white/10 rounded-full transition-colors mr-1"
            aria-expanded={isOpen}
            aria-controls="menu-mobile"
            aria-label={isOpen ? "Fechar menu" : "Abrir menu"}
            onClick={() => setIsOpen((current) => !current)}
          >
            {isOpen ? <X aria-hidden="true" className="w-6 h-6" /> : <Menu aria-hidden="true" className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isOpen && (
          <div id="menu-mobile" className="absolute top-[110%] left-4 right-4 bg-[#1A2E26] border border-white/10 rounded-3xl shadow-xl overflow-hidden flex flex-col p-4 z-50">
            <nav aria-label="Navegação móvel" className="flex flex-col gap-2">
              {links.map(([label, href]) => (
                <a
                  key={href}
                  href={href}
                  className="px-4 py-3 text-white/90 hover:text-white hover:bg-white/5 rounded-xl font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  {label}
                </a>
              ))}
            </nav>
            <div className="flex flex-col gap-3 mt-4 pt-4 border-t border-white/10 px-4">
              <Link
                href="/login"
                className="py-3 text-center text-white font-medium hover:bg-white/5 rounded-xl transition-colors"
                onClick={() => setIsOpen(false)}
              >
                Entrar
              </Link>
              <Link
                href="/register"
                className="group flex justify-between items-center bg-[#F97316] text-white pl-5 pr-2 py-2 rounded-full font-bold hover:bg-[#EA580C] transition-colors"
                onClick={() => setIsOpen(false)}
              >
                Cadastre-se
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[#1A2E26] group-hover:scale-105 transition-transform">
                  <ArrowRight className="w-4 h-4 text-white" />
                </span>
              </Link>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
