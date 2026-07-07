"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { BarChart2, Calendar, ChevronLeft, ChevronRight, DollarSign, FileText, Home, LogOut, MessageSquare, Settings, Users } from "lucide-react";

import { useAuth } from "@/contexts/auth";
import { cn } from "@/lib/utils";

interface SidebarProps {
  className?: string;
}

const items: Array<{ name: string; href: string; icon: React.ComponentType<{ className?: string }>; roles?: string[] }> = [
  { name: "Visão geral", href: "/dashboard", icon: Home },
  { name: "Agenda", href: "/dashboard/agenda", icon: Calendar },
  { name: "Pacientes", href: "/dashboard/patients", icon: Users },
  { name: "Documentos", href: "/dashboard/documentos", icon: FileText, roles: ["therapist", "admin"] },
  { name: "Financeiro", href: "/dashboard/financeiro", icon: DollarSign },
  { name: "Relatórios", href: "/dashboard?view=reports", icon: BarChart2 },
  { name: "Comunicações", href: "#", icon: MessageSquare },
  { name: "Configurações", href: "#", icon: Settings },
];

export function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();
  const allowed = items.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  return (
    <aside className={cn("sticky top-0 z-30 flex h-screen flex-col justify-between border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-200", isCollapsed ? "w-20" : "w-64", className)}>
      <div>
        <div className={cn("flex items-center justify-between px-5 py-5", isCollapsed && "justify-center px-3")}>
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-sidebar-active/25 bg-sidebar-active/10 text-sidebar-active">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25" aria-hidden="true"><path d="M12 2 2 7l10 5 10-5-10-5ZM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
            </div>
            {!isCollapsed && <span className="text-base font-bold tracking-tight text-sidebar-foreground">Elo Terapêutico</span>}
          </div>
          {!isCollapsed && <button type="button" onClick={() => setIsCollapsed(true)} className="rounded-lg p-1.5 text-sidebar-muted transition hover:bg-sidebar-surface hover:text-sidebar-foreground" aria-label="Recolher menu lateral"><ChevronLeft className="h-4 w-4" /></button>}
        </div>

        <nav className="mt-4 space-y-1 px-3" aria-label="Navegação principal">
          {allowed.map((item) => {
            const Icon = item.icon;
            const reportsActive = item.href.includes("view=reports") && pathname === "/dashboard" && searchParams.get("view") === "reports";
            const isActive = reportsActive || pathname === item.href || (item.href !== "/dashboard" && item.href !== "#" && !item.href.includes("?") && pathname?.startsWith(`${item.href}/`));
            return (
              <Link key={item.name} href={item.href} className={cn("group relative flex items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 text-xs font-semibold transition", isActive ? "border-sidebar-active/15 bg-sidebar-active/10 text-sidebar-foreground" : "text-sidebar-muted hover:bg-sidebar-surface hover:text-sidebar-foreground", isCollapsed && "justify-center px-2")} aria-current={isActive ? "page" : undefined}>
                {isActive && <span className="absolute bottom-2 left-0 top-2 w-0.5 rounded-full bg-sidebar-active" />}
                <Icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-sidebar-active" : "text-sidebar-muted group-hover:text-sidebar-foreground")} />
                {!isCollapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="space-y-2 border-t border-sidebar-border p-3">
        {!isCollapsed && <div className="mb-2 flex items-center gap-3 rounded-lg border border-sidebar-border bg-sidebar-surface/70 px-3 py-3"><div className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-sidebar-active/25 bg-sidebar-active/10 text-xs font-bold text-sidebar-active">{user?.full_name?.charAt(0).toUpperCase() || "J"}</div><div className="min-w-0"><p className="truncate text-xs font-bold leading-tight text-sidebar-foreground">{user?.full_name || "Juliana Martins"}</p><span className="mt-0.5 block truncate text-[9px] text-sidebar-muted">Ver perfil</span></div></div>}
        {isCollapsed && <button type="button" onClick={() => setIsCollapsed(false)} className="flex w-full items-center justify-center rounded-lg p-2.5 text-sidebar-muted transition hover:bg-sidebar-surface hover:text-sidebar-foreground" aria-label="Expandir menu lateral"><ChevronRight className="h-4 w-4" /></button>}
        <button type="button" onClick={logout} className={cn("group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-xs font-semibold text-danger/80 transition hover:bg-danger-soft hover:text-danger", isCollapsed && "justify-center px-2")}><LogOut className="h-4 w-4 shrink-0 transition-transform group-hover:-translate-x-0.5" />{!isCollapsed && <span>Sair</span>}</button>
      </div>
    </aside>
  );
}
