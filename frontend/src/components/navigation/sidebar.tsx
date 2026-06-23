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
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
  LogOut,
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
    { name: "Início", href: "/dashboard", icon: Home },
    { name: "Pacientes", href: "/dashboard/patients", icon: Users },
    {
      name: "Prontuários",
      href: "/dashboard/records",
      icon: ClipboardList,
      roles: ["therapist", "admin"], // Proteção básica no nível da UI (middleware cuida da proteção de rotas real)
    },
    { name: "Agenda", href: "/dashboard/agenda", icon: Calendar },
    { name: "Financeiro", href: "/dashboard/financeiro", icon: DollarSign },
  ];

  const allowedMenuItems = menuItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside
      className={cn(
        "h-screen sticky top-0 bg-card border-r border-border/40 flex flex-col justify-between transition-all duration-300 z-30",
        isCollapsed ? "w-20" : "w-64",
        className
      )}
    >
      {/* Topo / Logo */}
      <div>
        <div className={cn("p-5 flex items-center justify-between", isCollapsed && "justify-center")}>
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 shrink-0 rounded-md bg-primary flex items-center justify-center">
              <Activity className="h-4.5 w-4.5 text-white" />
            </div>
            {!isCollapsed && (
              <span className="font-bold text-base tracking-tight text-foreground">
                Elo Terapêutico
              </span>
            )}
          </div>
          
          {!isCollapsed && (
            <button
              onClick={() => setIsCollapsed(true)}
              className="text-muted-foreground hover:text-foreground hover:bg-secondary/80 rounded-md p-1 transition-all cursor-pointer"
            >
              <ChevronLeft className="h-4.5 w-4.5" />
            </button>
          )}
        </div>

        {/* Menu de Navegação */}
        <nav className="px-3 space-y-1 mt-6">
          {allowedMenuItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-150 group relative",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                )}
              >
                <Icon className={cn("h-4.5 w-4.5 shrink-0", isActive ? "text-white" : "text-muted-foreground group-hover:text-foreground")} />
                {!isCollapsed && <span>{item.name}</span>}
                
                {/* Tooltip quando colapsado */}
                {isCollapsed && (
                  <div className="absolute left-full ml-4 px-2 py-1 bg-card border border-border text-foreground text-xs font-medium rounded-sm opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none whitespace-nowrap shadow-xs z-50">
                    {item.name}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Rodapé / Perfil & Logout */}
      <div className="p-3 border-t border-border/40 space-y-1">
        {/* Toggle para abrir se tiver colapsado */}
        {isCollapsed && (
          <button
            onClick={() => setIsCollapsed(false)}
            className="w-full flex items-center justify-center p-2.5 text-muted-foreground hover:text-foreground hover:bg-secondary/60 rounded-md transition-all cursor-pointer"
          >
            <ChevronRight className="h-4.5 w-4.5" />
          </button>
        )}

        <button
          onClick={logout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium text-destructive/80 hover:text-destructive hover:bg-destructive/5 transition-all cursor-pointer group relative"
          )}
        >
          <LogOut className="h-4.5 w-4.5 shrink-0 group-hover:translate-x-[-1px] transition-transform duration-150" />
          {!isCollapsed && <span>Sair</span>}
          
          {isCollapsed && (
            <div className="absolute left-full ml-4 px-2 py-1 bg-destructive text-destructive-foreground text-xs font-medium rounded-sm opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none whitespace-nowrap shadow-xs z-50">
              Sair
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}
