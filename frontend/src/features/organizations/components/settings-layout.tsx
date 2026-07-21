"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const links = [
  ["/dashboard/configuracoes/organizacao", "Organização"],
  ["/dashboard/configuracoes/equipe", "Equipe"],
  ["/dashboard/configuracoes/perfil-profissional", "Perfil profissional"],
  ["/dashboard/configuracoes/atendimento", "Atendimento"],
] as const;

export function OrganizationSettingsLayout({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </header>
      <nav className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-card p-1">
        {links.map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className={`whitespace-nowrap rounded-lg px-4 py-2 text-xs font-medium transition ${
              pathname === href
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>
      <section className="rounded-2xl border border-border bg-card p-5 shadow-sm md:p-7">
        {children}
      </section>
    </div>
  );
}
