"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { Brand } from "./brand";

const links = [
  ["Produto", "#produto"],
  ["Como funciona", "#fluxo"],
  ["Módulos", "#modulos"],
  ["Segurança", "#seguranca"],
  ["Perguntas", "#faq"],
] as const;

export function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  return (
    <header className="site-header">
      <a href="#conteudo" className="site-header__skip">Pular para o conteúdo</a>
      <div className="site-header__inner">
        <Brand compact />

        <nav aria-label="Navegação principal" className="site-header__nav">
          {links.map(([label, href]) => <a key={href} href={href}>{label}</a>)}
        </nav>

        <div className="site-header__actions">
          <Link href="/login">Entrar</Link>
          <Link href="/register" className="site-header__cta">
            Começar agora <ArrowRight aria-hidden="true" />
          </Link>
        </div>

        <button
          type="button"
          className="site-header__menu"
          aria-expanded={isOpen}
          aria-controls="menu-mobile"
          aria-label={isOpen ? "Fechar menu" : "Abrir menu"}
          onClick={() => setIsOpen((current) => !current)}
        >
          {isOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
        </button>
      </div>

      {isOpen && (
        <div id="menu-mobile" className="site-header__mobile">
          <nav aria-label="Navegação móvel">
            {links.map(([label, href]) => (
              <a key={href} href={href} onClick={() => setIsOpen(false)}>{label}</a>
            ))}
          </nav>
          <div>
            <Link href="/login">Entrar</Link>
            <Link href="/register">Criar conta</Link>
          </div>
        </div>
      )}
    </header>
  );
}
