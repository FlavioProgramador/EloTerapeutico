"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Brand } from "./brand";
import { navigationLinks } from "./content";

export function SiteHeader() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 sm:px-8">
        <Brand compact />

        <nav aria-label="Navegação principal" className="hidden items-center gap-2 lg:flex">
          {navigationLinks.map((item) => (
            <a key={item.href} href={item.href} className="rounded-lg px-3 py-2 text-sm font-semibold text-muted-foreground hover:bg-secondary hover:text-foreground">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 sm:flex">
          <Link href="/login" className="rounded-lg px-4 py-2 text-sm font-bold text-foreground hover:bg-secondary">
            Entrar
          </Link>
          <Link href="/register" className="rounded-xl bg-primary px-5 py-3 text-sm font-extrabold text-primary-foreground hover:opacity-90">
            Criar conta
          </Link>
        </div>

        <button type="button" aria-expanded={isOpen} aria-controls="menu-mobile" aria-label={isOpen ? "Fechar menu" : "Abrir menu"} onClick={() => setIsOpen(!isOpen)} className="grid h-11 w-11 place-items-center rounded-xl border border-border bg-secondary text-foreground sm:hidden">
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {isOpen && (
        <div id="menu-mobile" className="border-t border-border bg-background px-5 pb-6 pt-4 sm:hidden">
          <nav aria-label="Navegação móvel" className="grid gap-1">
            {navigationLinks.map((item) => (
              <a key={item.href} href={item.href} onClick={() => setIsOpen(false)} className="rounded-xl px-4 py-3 text-sm font-bold text-muted-foreground hover:bg-secondary hover:text-foreground">
                {item.label}
              </a>
            ))}
          </nav>
          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-border pt-4">
            <Link href="/login" className="inline-flex min-h-11 items-center justify-center rounded-xl border border-border px-4 text-sm font-bold text-foreground">Entrar</Link>
            <Link href="/register" className="inline-flex min-h-11 items-center justify-center rounded-xl bg-primary px-4 text-sm font-extrabold text-primary-foreground">Criar conta</Link>
          </div>
        </div>
      )}
    </header>
  );
}
