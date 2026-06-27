"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Users,
  ClipboardList,
  Calendar,
  DollarSign,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Settings,
  MessageSquare,
  BarChart2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/auth";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const menuItems = [
    { name: "Visão geral", href: "/dashboard", icon: Home },
    { name: "Agenda", href: "/dashboard/agenda", icon: Calendar },
    { name: "Pacientes", href: "/dashboard/patients", icon: Users },
    {
      name: "Prontuários",
      href: "/dashboard/records",
      icon: ClipboardList,
      roles: ["therapist", "admin"],
    },
    { name: "Financeiro", href: "/dashboard/financeiro", icon: DollarSign },
    { name: "Relatórios", href: "#", icon: BarChart2 },
    { name: "Comunicações", href: "#", icon: MessageSquare },
    { name: "Configurações", href: "#", icon: Settings },
  ];

  const allowedMenuItems = menuItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside
      className={cn(
        "h-screen sticky top-0 bg-[hsl(165,38%,10%)] border-r border-[hsl(165,27%,16%)] flex flex-col justify-between transition-all duration-300 z-30",
        isCollapsed ? "w-20" : "w-64",
        className
      )}
    >
      {/* Topo / Logo */}
      <div>
        <div className={cn("p-6 flex items-center justify-between", isCollapsed && "justify-center")}>
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 shrink-0 rounded-lg bg-[hsl(38,25%,87%)]/10 flex items-center justify-center text-[hsl(38,25%,87%)]">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            {!isCollapsed && (
              <span className="font-bold text-base tracking-tight text-[hsl(40,20%,94%)]">
                Elo Terapêutico
              </span>
            )}
          </div>
          
          {!isCollapsed && (
            <button
              onClick={() => setIsCollapsed(true)}
              className="text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] rounded-lg p-1 transition-all cursor-pointer"
            >
              <ChevronLeft className="h-4.5 w-4.5" />
            </button>
          )}
        </div>

        {/* Menu de Navegação */}
        <nav className="px-4 space-y-1.5 mt-6 text-left">
          {allowedMenuItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href + "/"));
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 group relative",
                  isActive
                    ? "bg-[hsl(38,25%,87%)]/10 text-[hsl(40,20%,94%)] border-l-2 border-[hsl(163,27%,62%)] pl-2.5"
                    : "text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)]"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-[hsl(163,27%,62%)]" : "text-[hsl(163,8%,68%)] group-hover:text-[hsl(40,20%,94%)]")} />
                {!isCollapsed && <span>{item.name}</span>}
                
                {/* Tooltip quando colapsado */}
                {isCollapsed && (
                  <div className="absolute left-full ml-4 px-2.5 py-1.5 bg-[hsl(165,38%,10%)] border border-[hsl(165,27%,16%)] text-[hsl(40,20%,94%)] text-[10px] font-semibold rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none whitespace-nowrap shadow-md z-50">
                    {item.name}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Rodapé / Perfil & Logout */}
      <div className="p-4 border-t border-[hsl(165,27%,16%)]/40 space-y-2 text-left">
        
        {/* Dados do Perfil */}
        {!isCollapsed && (
          <div className="flex items-center gap-3 px-2 py-2 mb-2">
            <div className="h-9 w-9 rounded-full bg-[hsl(38,25%,87%)]/10 border border-[hsl(38,25%,87%)]/20 flex items-center justify-center text-[hsl(38,25%,87%)] font-bold text-xs shrink-0">
              {user?.full_name?.charAt(0).toUpperCase() || "J"}
            </div>
            <div className="truncate">
              <p className="text-xs font-bold text-[hsl(40,20%,94%)] truncate leading-tight">
                {user?.full_name || "Juliana Martins"}
              </p>
              <span className="text-[9px] text-[hsl(163,8%,68%)] block hover:text-[hsl(40,20%,94%)] cursor-pointer">
                Ver perfil
              </span>
            </div>
          </div>
        )}

        {/* Toggle para abrir se tiver colapsado */}
        {isCollapsed && (
          <button
            onClick={() => setIsCollapsed(false)}
            className="w-full flex items-center justify-center p-2.5 text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] rounded-lg transition-all cursor-pointer"
          >
            <ChevronRight className="h-4.5 w-4.5" />
          </button>
        )}

        <button
          onClick={logout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-500/5 transition-all cursor-pointer group relative"
          )}
        >
          <LogOut className="h-4 w-4 shrink-0 group-hover:translate-x-[-1px] transition-transform duration-150" />
          {!isCollapsed && <span>Sair</span>}
          
          {isCollapsed && (
            <div className="absolute left-full ml-4 px-2 py-1 bg-red-950/60 border border-red-500/20 text-red-400 text-[10px] font-semibold rounded-md opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none whitespace-nowrap shadow-md z-50">
              Sair
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}
