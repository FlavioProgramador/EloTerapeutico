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
    const timeoutId = setTimeout(() => {
      setTheme(isDark ? "dark" : "light");
    }, 0);
    return () => clearTimeout(timeoutId);
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
        "h-16 border-b border-[hsl(165,27%,16%)] bg-[hsl(165,40%,7%)] sticky top-0 z-20 flex items-center justify-between px-6 transition-colors duration-150",
        className
      )}
    >
      {/* Busca Global */}
      <div className="relative w-full max-w-md hidden md:block">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(163,8%,68%)]/60" />
        <input
          type="text"
          placeholder="Buscar pacientes, consultas, prontuários..."
          className="w-full h-9 bg-[hsl(165,27%,12%)] border border-[hsl(165,27%,16%)] rounded-lg pl-10 pr-4 text-xs text-[hsl(40,20%,94%)] placeholder:text-[hsl(163,8%,68%)]/50 focus:outline-none focus:border-[hsl(38,25%,87%)] transition-colors"
        />
      </div>

      {/* Ações do Header */}
      <div className="flex items-center gap-4 ml-auto">
        {/* Toggle Light/Dark Mode */}
        <button
          onClick={toggleTheme}
          className="h-10 w-10 flex items-center justify-center text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] rounded-lg transition-all cursor-pointer"
          title="Alternar Tema"
        >
          {theme === "light" ? <Moon className="h-4.5 w-4.5" /> : <Sun className="h-4.5 w-4.5" />}
        </button>

        {/* Notificações */}
        <button
          className="h-10 w-10 flex items-center justify-center text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] rounded-lg relative transition-all cursor-pointer"
          title="Notificações"
        >
          <Bell className="h-4.5 w-4.5" />
          <span className="absolute top-2 right-2.5 h-1.5 w-1.5 rounded-full bg-[hsl(163,27%,62%)]" />
        </button>

        <div className="h-6 w-[1px] bg-[hsl(165,27%,16%)]" />

        {/* Dropdown de Perfil */}
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="flex items-center gap-3 hover:bg-[hsl(165,27%,12%)] rounded-lg p-1.5 transition-all cursor-pointer"
          >
            {/* Avatar Genérico */}
            <div className="h-8.5 w-8.5 rounded-full bg-[hsl(38,25%,87%)]/10 border border-[hsl(38,25%,87%)]/20 flex items-center justify-center text-[hsl(38,25%,87%)] font-bold text-xs">
              {user?.full_name?.charAt(0).toUpperCase() || "J"}
            </div>
            
            <div className="text-left hidden sm:block">
              <p className="text-xs font-bold leading-none text-[hsl(40,20%,94%)]">
                {user?.full_name || "Juliana Martins"}
              </p>
              <p className="text-[10px] text-[hsl(163,8%,68%)] mt-0.5">
                {user ? getRoleLabel(user.role) : "Terapeuta"}
              </p>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-[hsl(163,8%,68%)] hidden sm:block" />
          </button>

          {/* Menu Dropdown do Perfil */}
          {isProfileOpen && (
            <>
              {/* Overlay invisível para fechar */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setIsProfileOpen(false)}
              />
              
              <div className="absolute right-0 mt-2 w-56 bg-[hsl(165,38%,10%)] border border-[hsl(165,27%,16%)] rounded-xl shadow-lg py-1.5 z-50 animate-fade-in">
                <div className="px-4 py-2 border-b border-[hsl(165,27%,16%)]/40">
                  <p className="text-xs font-bold text-[hsl(40,20%,94%)] truncate">
                    {user?.full_name || "Juliana Martins"}
                  </p>
                  <p className="text-[10px] text-[hsl(163,8%,68%)] truncate mt-0.5">
                    {user?.email || "juliana@teste.com"}
                  </p>
                </div>
                
                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] transition-all text-left cursor-pointer"
                  >
                    <User className="h-4 w-4" />
                    Meu Perfil
                  </button>
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-[hsl(163,8%,68%)] hover:text-[hsl(40,20%,94%)] hover:bg-[hsl(165,27%,12%)] transition-all text-left cursor-pointer"
                  >
                    <Settings className="h-4 w-4" />
                    Configurações
                  </button>
                </div>

                <div className="border-t border-[hsl(165,27%,16%)]/40 my-1" />

                <div className="py-1">
                  <button
                    onClick={() => {
                      setIsProfileOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/5 transition-all text-left cursor-pointer"
                  >
                    <LogOut className="h-4 w-4" />
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
