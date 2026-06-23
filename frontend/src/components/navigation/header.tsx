"use client";

import React, { useState, useEffect } from "react";
import { Search, Sun, Moon, Bell, ChevronDown, User, LogOut, Settings } from "lucide-react";
import { useAuth } from "@/contexts/auth";
import { cn } from "@/lib/utils";

interface HeaderProps {
  className?: string;
}

export function Header({ className }: HeaderProps) {
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Inicializa o tema baseado no estado atual
  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
  }, []);

  const toggleTheme = () => {
    if (theme === "light") {
      document.documentElement.classList.add("dark");
      setTheme("dark");
    } else {
      document.documentElement.classList.remove("dark");
      setTheme("light");
    }
  };

  const getRoleLabel = (role: string) => {
    const roles: Record<string, string> = {
      therapist: "Terapeuta",
      secretary: "Secretária",
      admin: "Administrador",
    };
    return roles[role] || role;
  };

  return (
    <header
      className={cn(
        "h-16 border-b border-border/40 bg-card/85 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between px-6 transition-all duration-300",
        className
      )}
    >
      {/* Busca Global */}
      <div className="relative w-full max-w-md hidden md:block">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4.5 w-4.5 text-muted-foreground/60" />
        <input
          type="text"
          placeholder="Buscar pacientes, consultas, prontuários..."
          className="w-full h-10 bg-secondary/40 border border-border/50 rounded-lg pl-11 pr-4 text-sm transition-all focus:outline-hidden focus:border-primary focus:ring-2 focus:ring-primary/10 placeholder:text-muted-foreground/50"
        />
      </div>

      {/* Ações do Header */}
      <div className="flex items-center gap-4 ml-auto">
        {/* Toggle Light/Dark Mode */}
        <button
          onClick={toggleTheme}
          className="h-10 w-10 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary/80 rounded-lg transition-all cursor-pointer"
          title="Alternar Tema"
        >
          {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </button>

        {/* Notificações */}
        <button
          className="h-10 w-10 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-secondary/80 rounded-lg relative transition-all cursor-pointer"
          title="Notificações"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute top-2 right-2.5 h-2 w-2 rounded-full bg-primary" />
        </button>

        <div className="h-6 w-[1px] bg-border/60" />

        {/* Dropdown de Perfil */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-3 hover:bg-secondary/60 rounded-lg p-1.5 transition-all cursor-pointer"
          >
            {/* Avatar Genérico */}
            <div className="h-8.5 w-8.5 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold text-sm">
              {user?.full_name?.charAt(0).toUpperCase() || "U"}
            </div>
            
            <div className="text-left hidden sm:block">
              <p className="text-sm font-semibold leading-none text-foreground">
                {user?.full_name || "Usuário"}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {user ? getRoleLabel(user.role) : ""}
              </p>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground hidden sm:block" />
          </button>

          {/* Menu Dropdown do Perfil */}
          {isProfileOpen && (
            <>
              {/* Overlay invisível para fechar */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setIsProfileOpen(false)}
              />
              
              <div className="absolute right-0 mt-2 w-56 bg-card border border-border/80 rounded-xl shadow-lg py-1.5 z-50 animate-fade-in">
                <div className="px-4 py-2 border-b border-border/40">
                  <p className="text-sm font-semibold text-foreground truncate">
                    {user?.full_name}
                  </p>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {user?.email}
                  </p>
                </div>
                
                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                      // TODO: Redirecionar para perfil nas próximas fases
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-all text-left cursor-pointer"
                  >
                    <User className="h-4.5 w-4.5" />
                    Meu Perfil
                  </button>
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-all text-left cursor-pointer"
                  >
                    <Settings className="h-4.5 w-4.5" />
                    Configurações
                  </button>
                </div>

                <div className="border-t border-border/40 my-1" />

                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-destructive/80 hover:text-destructive hover:bg-destructive/5 transition-all text-left cursor-pointer"
                  >
                    <LogOut className="h-4.5 w-4.5" />
                    Sair
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
